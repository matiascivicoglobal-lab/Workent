"""Orquestador: busca, normaliza, tasa, puntúa y avisa."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from . import cotizacion as fx
from .almacen import Almacen
from .fuentes import construir_fuentes
from .mensajes import alerta as armar_alerta, recortar, resumen_diario
from .navegador import Navegador, disponible as hay_navegador
from .notificadores import construir_notificador
from .red import Cliente
from .scoring import Evaluador, pasa_filtros_basicos
from .tasacion import Tasador
from .util import ahora, dias_desde, parse_fecha

log = logging.getLogger("radar")


@dataclass
class Resultado:
    revisados: int = 0
    nuevos: int = 0
    descartados: int = 0
    oportunidades: list = field(default_factory=list)
    enviados: int = 0
    por_fuente: dict = field(default_factory=dict)
    errores: list = field(default_factory=list)

    def como_dict(self) -> dict:
        return {"revisados": self.revisados, "nuevos": self.nuevos,
                "descartados": self.descartados,
                "oportunidades": len(self.oportunidades),
                "enviados": self.enviados, "por_fuente": self.por_fuente}


class Radar:
    def __init__(self, ajustes, enviar: bool = True, canal: str = ""):
        self.cfg = ajustes
        self.enviar = enviar
        self.almacen = Almacen(ajustes.db)
        self.cliente = Cliente(
            demora=float(ajustes.get("scraping.demora_entre_pedidos", 2.5)),
            timeout=float(ajustes.get("scraping.timeout", 30)),
            reintentos=int(ajustes.get("scraping.reintentos", 3)),
            proxy=ajustes.secreto("RADAR_PROXY") or None,
        )
        self.tasador = Tasador(self.almacen, ajustes)
        self.evaluador = Evaluador(self.tasador, ajustes)
        self.notificador = construir_notificador(ajustes, canal=canal)
        self._navegador: Navegador | None = None
        self._fuentes: list | None = None
        self.usd_ars = 0.0

    # ------------------------------------------------------------------
    def navegador(self) -> Navegador | None:
        """Se abre una sola vez y solo si alguna fuente activa lo necesita."""
        if self._navegador is not None:
            return self._navegador
        necesita = any(self.cfg.fuente_usa_navegador(f) for f in self.cfg.fuentes_activas)
        if not necesita:
            return None
        if not hay_navegador():
            log.warning("Playwright no está instalado: quedan fuera %s",
                        [f for f in self.cfg.fuentes_activas
                         if self.cfg.fuente_usa_navegador(f)])
            return None
        perfil = self.cfg.get("fuentes.facebook.activa") and \
            self.cfg.ruta_datos("datos/perfil_chromium")
        self._navegador = Navegador(
            headless=not self.cfg.get("scraping.navegador_visible", False),
            perfil=perfil or None,
            demora=float(self.cfg.get("scraping.demora_entre_pedidos", 2.5)),
        ).abrir()
        return self._navegador

    def cerrar(self) -> None:
        self.cliente.cerrar()
        if self._navegador:
            self._navegador.cerrar()
        self.almacen.cerrar()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()

    # ==================================================================
    def correr(self) -> Resultado:
        res = Resultado()
        self.usd_ars = fx.obtener(
            self.cliente, self.almacen,
            tipo=str(self.cfg.get("monitoreo.cotizacion", "blue")),
            manual=float(self.cfg.get("monitoreo.usd_ars_manual", 1450)))

        # --- 1. recolectar ------------------------------------------------
        crudos = self._recolectar(res)

        # --- 2. guardar (la tasación necesita el corpus completo) ---------
        cambios = self._guardar(crudos, res)
        self.tasador.invalidar()

        # --- 3. evaluar ---------------------------------------------------
        evaluaciones = self._evaluar(crudos, cambios)
        res.oportunidades = [ev for ev in evaluaciones if self.evaluador.merece_alerta(ev)]
        res.oportunidades.sort(key=lambda e: e.puntaje, reverse=True)

        # --- 4. avisar ----------------------------------------------------
        if self.enviar:
            res.enviados = self._avisar(res.oportunidades, cambios)

        self.almacen.marcar_inactivos(dias=21)
        log.info("Corrida terminada: %s", res.como_dict())
        return res

    # ------------------------------------------------------------------
    def fuentes(self) -> list:
        """Se arman una sola vez: MercadoLibre descubre sus filtros al crearse."""
        if self._fuentes is None:
            self._fuentes = construir_fuentes(self.cfg.fuentes_activas, self.cliente,
                                              self.cfg, self.navegador())
        return self._fuentes

    def _recolectar(self, res: Resultado) -> list:
        fuentes = self.fuentes()
        todos = []
        for fuente in fuentes:
            if self._demasiado_pronto(fuente.nombre):
                continue
            total_fuente = 0
            for barrio in self.cfg.barrios:
                avisos = fuente.seguro(barrio)
                for a in avisos:
                    a.precio_usd = fx.a_usd(a.precio, a.moneda, self.usd_ars)
                todos.extend(avisos)
                total_fuente += len(avisos)
            res.por_fuente[fuente.nombre] = total_fuente
            self.almacen.registrar_corrida(fuente.nombre, total_fuente, 0)
            if total_fuente == 0:
                res.errores.append(f"{fuente.nombre} no devolvió avisos")
        res.revisados = len(todos)
        return todos

    def _demasiado_pronto(self, fuente: str) -> bool:
        """Algunas fuentes conviene consultarlas espaciadas (Facebook, sobre todo).
        Se configura con fuentes.<nombre>.cada_minutos."""
        cada = self.cfg.get(f"fuentes.{fuente}.cada_minutos")
        if not cada:
            return False
        ultima = parse_fecha(self.almacen.ultima_corrida(fuente))
        if not ultima:
            return False
        minutos = (ahora() - ultima).total_seconds() / 60
        if minutos < float(cada):
            log.info("  salteo %s: la consulté hace %.0f min (mínimo %s)",
                     fuente, minutos, cada)
            return True
        return False

    # ------------------------------------------------------------------
    def _guardar(self, avisos: list, res: Resultado) -> dict:
        cambios: dict[str, dict] = {}
        vistos: set[str] = set()
        for a in avisos:
            if a.id in vistos:
                continue
            vistos.add(a.id)
            cambio = self.almacen.guardar(a)
            cambios[a.id] = cambio
            if cambio["nuevo"]:
                res.nuevos += 1
        return cambios

    # ------------------------------------------------------------------
    def _evaluar(self, avisos: list, cambios: dict) -> list:
        enriquecer = bool(self.cfg.get("scraping.enriquecer_candidatos", True))
        tope = int(self.cfg.get("scraping.max_enriquecer", 15))
        fuentes = {f.nombre: f for f in self.fuentes()}

        evaluaciones, candidatos = [], []
        vistos: set[str] = set()
        for a in avisos:
            if a.id in vistos:
                continue
            vistos.add(a.id)

            motivo = pasa_filtros_basicos(a, self.cfg)
            if motivo:
                log.debug("  descarto %s: %s", a.id, motivo)
                continue

            baja = self.almacen.baja_de_precio(a.id)
            dias_visible = dias_desde(parse_fecha(self.almacen.primera_vez(a.id)))
            ev = self.evaluador.evaluar(a, baja_precio=baja, dias_visible=dias_visible)
            if ev.motivo_descarte:
                log.debug("  descarto %s: %s", a.id, ev.motivo_descarte)
                continue
            evaluaciones.append(ev)

            # Candidato = está cerca del umbral; vale la pena abrir la ficha.
            cerca = (ev.puntaje >= self.evaluador.puntaje_minimo * 0.75 or
                     (ev.descuento or 0) >= self.evaluador.desc_minimo * 0.75)
            if cerca and a.fuente in fuentes:
                candidatos.append((len(evaluaciones) - 1, ev))

        if enriquecer and candidatos:
            candidatos.sort(key=lambda par: par[1].puntaje, reverse=True)
            for idx, ev in candidatos[:tope]:
                try:
                    fuentes[ev.aviso.fuente].enriquecer(ev.aviso)
                except Exception as e:              # noqa: BLE001
                    log.debug("  no pude enriquecer %s: %s", ev.aviso.id, e)
                    continue
                self.almacen.guardar(ev.aviso)
                evaluaciones[idx] = self.evaluador.evaluar(
                    ev.aviso, baja_precio=ev.baja_precio,
                    dias_visible=ev.dias_publicado)

        return evaluaciones

    # ------------------------------------------------------------------
    def _avisar(self, oportunidades: list, cambios: dict) -> int:
        if not self._en_horario():
            log.info("Fuera del horario de avisos: guardo %d oportunidades para después",
                     len(oportunidades))
            return 0

        listo, falta = self.notificador.configurado()
        if not listo:
            log.error("No puedo avisar: %s", falta)
            return 0

        tope = int(self.cfg.get("alertas.max_por_corrida", 6))
        reenviar = bool(self.cfg.get("alertas.reenviar_si_baja_precio", True))
        baja_min = float(self.cfg.get("alertas.baja_precio_minima", 0.04))

        enviados = 0
        ya_en_esta_corrida: set[str] = set()
        for ev in oportunidades:
            if enviados >= tope:
                log.info("Llegué al tope de %d avisos por corrida; el resto queda "
                         "en el reporte", tope)
                break
            a = ev.aviso

            # El mismo depto suele estar en 3 portales: avisamos una sola vez.
            clave = a.clave_dedupe()
            if clave in ya_en_esta_corrida:
                continue
            duplicados = self.almacen.duplicados_de(a)
            if any(self.almacen.ya_alertado(d) for d in duplicados):
                log.debug("  %s ya avisado por otro portal", a.id)
                continue

            tipo = "nueva"
            if self.almacen.ya_alertado(a.id, "nueva"):
                baja = ev.baja_precio
                if not (reenviar and baja and baja["pct"] >= baja_min):
                    continue
                if self.almacen.ya_alertado(a.id, f"baja_{baja['hasta']:.0f}"):
                    continue
                tipo = "baja_precio"

            mensaje = recortar(armar_alerta(ev, tipo))
            if self.notificador.enviar(mensaje):
                enviados += 1
                ya_en_esta_corrida.add(clave)
                self.almacen.registrar_alerta(a.id, tipo, ev.puntaje,
                                              f"{ev.descuento:.3f}" if ev.descuento else "")
                if tipo == "baja_precio":
                    self.almacen.registrar_alerta(
                        a.id, f"baja_{ev.baja_precio['hasta']:.0f}", ev.puntaje)
            else:
                log.error("Falló el envío de %s; lo reintento en la próxima corrida", a.id)
        return enviados

    # ------------------------------------------------------------------
    def _en_horario(self) -> bool:
        rango = self.cfg.get("monitoreo.horario_activo", [0, 24])
        try:
            desde, hasta = int(rango[0]), int(rango[1])
        except (TypeError, ValueError, IndexError):
            return True
        hora = datetime.now().hour
        return desde <= hora < hasta

    # ------------------------------------------------------------------
    def enviar_resumen(self, res: Resultado) -> bool:
        refs = self.tasador.todas(self.cfg.barrios)
        mensaje = recortar(resumen_diario(res.oportunidades, refs, res.como_dict()))
        return self.notificador.enviar(mensaje)
