"""Scoring de oportunidad: ¿cuánto vale la pena mirar este aviso?

La idea: una propiedad a reciclar TIENE que estar por debajo de la mediana
(ese descuento es el costo de la obra). La oportunidad real es el descuento
que sobra DESPUÉS de descontar la reforma, los impuestos y la comisión.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tasacion import Referencia
from .util import normalizar

# --- Señales en el texto del aviso -----------------------------------------
# Cada tupla: (patrón a buscar, etiqueta legible, peso 0-1)
SENIALES_OPORTUNIDAD = [
    ("a reciclar", "a reciclar", 1.0),
    ("para reciclar", "a reciclar", 1.0),
    ("a refaccionar", "a refaccionar", 1.0),
    ("para refaccionar", "a refaccionar", 1.0),
    ("a remodelar", "a remodelar", 1.0),
    ("para remodelar", "a remodelar", 1.0),
    ("necesita refaccion", "necesita refacción", 1.0),
    ("necesita reforma", "necesita reforma", 1.0),
    ("a poner en valor", "a poner en valor", 0.9),
    ("estado original", "estado original", 0.8),
    ("para refaccionar a gusto", "a refaccionar", 1.0),
    ("ideal inversor", "ideal inversor", 0.6),
    ("ideal inversion", "ideal inversión", 0.6),
    ("mucho potencial", "con potencial", 0.5),
    ("dueno directo", "dueño directo", 0.8),
    ("dueno vende", "dueño directo", 0.8),
    ("sin comision", "sin comisión", 0.6),
    ("sucesion", "sucesión", 0.7),
    ("escucho ofertas", "escucha ofertas", 0.9),
    ("recibo ofertas", "escucha ofertas", 0.9),
    ("urge", "urgencia de venta", 0.9),
    ("urgente", "urgencia de venta", 0.9),
    ("permuta", "acepta permuta", 0.4),
    ("oportunidad", "se publicita como oportunidad", 0.3),
    ("rebajado", "precio rebajado", 0.8),
    ("bajo de precio", "precio rebajado", 0.8),
    ("apto credito", "apto crédito", 0.5),
]

SENIALES_RIESGO = [
    ("nuda propiedad", "nuda propiedad (no podés usarlo)", 1.0),
    ("usufructo", "con usufructo vitalicio", 1.0),
    ("ocupado", "ocupado", 1.0),
    ("intrusado", "intrusado", 1.0),
    ("sin escritura", "sin escritura", 1.0),
    ("cesion de derechos", "cesión de derechos, no escritura", 1.0),
    ("posesion", "se vende posesión", 0.9),
    ("boleto de compraventa", "solo boleto", 0.7),
    ("juicio", "en juicio", 0.8),
    ("sucesion en tramite", "sucesión en trámite (demora)", 0.5),
    ("en pozo", "en pozo", 1.0),
    ("en construccion", "en construcción", 0.8),
    ("fideicomiso", "fideicomiso", 0.7),
    ("no apto credito", "no apto crédito", 0.4),
    ("club de campo", "no es CABA", 1.0),
    ("tiempo compartido", "tiempo compartido", 1.0),
]


@dataclass
class Evaluacion:
    aviso: object
    referencia: Referencia | None
    precio_m2: float | None = None
    descuento: float | None = None          # 0.38 = 38% bajo la mediana
    costo_reforma: float = 0.0
    inversion_total: float = 0.0
    valor_objetivo: float = 0.0             # valor reciclado (p75 de la zona)
    valor_neto: float = 0.0                 # descontada la comisión de venta
    margen: float = 0.0
    margen_pct: float = 0.0
    puntaje: float = 0.0
    senales: list[str] = field(default_factory=list)
    riesgos: list[str] = field(default_factory=list)
    sospechoso: bool = False
    baja_precio: dict | None = None
    dias_publicado: int | None = None
    motivo_descarte: str = ""

    @property
    def confianza(self) -> str:
        return self.referencia.confianza if self.referencia else "baja"

    @property
    def es_oportunidad(self) -> bool:
        return not self.motivo_descarte and self.puntaje > 0


def _buscar_senales(texto: str, catalogo) -> tuple[dict[str, float], float]:
    """Devuelve {etiqueta: peso} y la suma de pesos."""
    encontradas: dict[str, float] = {}
    for patron, etiqueta, peso in catalogo:
        if patron in texto:
            encontradas[etiqueta] = max(encontradas.get(etiqueta, 0), peso)
    return encontradas, sum(encontradas.values())


def _acotar(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class Evaluador:
    def __init__(self, tasador, ajustes):
        self.tasador = tasador
        self.cfg = ajustes
        o = "oportunidad."
        self.costo_reforma_m2 = float(ajustes.get(o + "costo_reforma_usd_m2", 400))
        self.costos_compra = float(ajustes.get(o + "costos_compra_pct", 0.06))
        self.costos_venta = float(ajustes.get(o + "costos_venta_pct", 0.04))
        self.desc_minimo = float(ajustes.get(o + "descuento_minimo", 0.18))
        self.puntaje_minimo = float(ajustes.get(o + "puntaje_minimo", 55))
        self.desc_sospechoso = float(ajustes.get(o + "descuento_sospechoso", 0.60))

    # ------------------------------------------------------------------
    def evaluar(self, aviso, baja_precio: dict | None = None,
                dias_visible: int | None = None) -> Evaluacion:
        ev = Evaluacion(aviso=aviso, referencia=None, baja_precio=baja_precio)
        ev.dias_publicado = aviso.dias_publicado() or dias_visible

        texto = aviso.texto_completo()
        senales, peso_senales = _buscar_senales(texto, SENIALES_OPORTUNIDAD)
        riesgos, peso_riesgos = _buscar_senales(texto, SENIALES_RIESGO)
        ev.senales = sorted(senales, key=senales.get, reverse=True)
        ev.riesgos = sorted(riesgos, key=riesgos.get, reverse=True)

        # Peso 1.0 = la operación directamente no sirve: se descarta, no se castiga.
        excluyentes = [etq for etq, peso in riesgos.items() if peso >= 1.0]
        if excluyentes:
            ev.motivo_descarte = f"riesgo excluyente: {excluyentes[0]}"
            return ev

        if not aviso.precio_usd:
            ev.motivo_descarte = "sin precio publicado"
            return ev
        m2 = aviso.m2_ref()
        if not m2:
            ev.motivo_descarte = "sin superficie publicada"
            return ev

        ev.referencia = self.tasador.referencia(aviso.barrio, aviso.ambientes)
        if not ev.referencia:
            ev.motivo_descarte = f"sin referencia de precio para {aviso.barrio}"
            return ev

        ref = ev.referencia
        ev.precio_m2 = aviso.precio_usd / m2
        ev.descuento = (ref.mediana - ev.precio_m2) / ref.mediana

        # --- economía del reciclado -----------------------------------
        ev.costo_reforma = m2 * self.costo_reforma_m2
        ev.inversion_total = (aviso.precio_usd * (1 + self.costos_compra)) + ev.costo_reforma
        ev.valor_objetivo = m2 * ref.p75
        ev.valor_neto = ev.valor_objetivo * (1 - self.costos_venta)
        ev.margen = ev.valor_neto - ev.inversion_total
        ev.margen_pct = ev.margen / ev.inversion_total if ev.inversion_total else 0.0

        # --- puntaje ----------------------------------------------------
        p_desc = _acotar(ev.descuento / 0.40) * 40        # 40% abajo = puntaje lleno
        p_marg = _acotar(ev.margen_pct / 0.30) * 30       # 30% de margen = lleno
        p_sen = _acotar(peso_senales / 2.5) * 12
        p_dias = _acotar((ev.dias_publicado or 0) / 120) * 8   # más tiempo = más negociable
        p_baja = 0.0
        if baja_precio and baja_precio.get("pct", 0) >= 0.03:
            p_baja = _acotar(baja_precio["pct"] / 0.15) * 10

        puntaje = p_desc + p_marg + p_sen + p_dias + p_baja
        puntaje -= _acotar(peso_riesgos / 2.0) * 15        # riesgos no excluyentes
        if ref.confianza == "baja":
            puntaje *= 0.85                                # menos muestra, menos certeza
        elif ref.confianza == "media":
            puntaje *= 0.95

        # Demasiado barato = casi siempre error de carga o no es lo que dice.
        if ev.descuento >= self.desc_sospechoso:
            ev.sospechoso = True
            puntaje = min(puntaje, 70)

        ev.puntaje = round(_acotar(puntaje, 0, 100), 1)
        return ev

    # ------------------------------------------------------------------
    def merece_alerta(self, ev: Evaluacion) -> bool:
        if ev.motivo_descarte or ev.descuento is None:
            return False
        return ev.descuento >= self.desc_minimo and ev.puntaje >= self.puntaje_minimo


def pasa_filtros_basicos(aviso, ajustes) -> str:
    """Devuelve '' si pasa, o el motivo de descarte."""
    b = ajustes.busqueda
    if aviso.ambientes is not None:
        if aviso.ambientes < int(b.get("ambientes_min", 1)):
            return f"{aviso.ambientes} ambientes (pedís {b.get('ambientes_min')}+)"
        if aviso.ambientes > int(b.get("ambientes_max", 99)):
            return f"{aviso.ambientes} ambientes (máximo {b.get('ambientes_max')})"
    if aviso.precio_usd:
        if aviso.precio_usd < float(b.get("precio_usd_min", 0)):
            return "precio por debajo del rango (sospechoso)"
        if aviso.precio_usd > float(b.get("precio_usd_max", 1e12)):
            return "fuera de presupuesto"
    m2 = aviso.m2_ref()
    if m2:
        if m2 < float(b.get("m2_min", 0)):
            return f"{m2:.0f} m² es menos del mínimo"
        if m2 > float(b.get("m2_max", 1e6)):
            return f"{m2:.0f} m² supera el máximo"
    tipos = [normalizar(t) for t in b.get("tipos", [])]
    if tipos and normalizar(aviso.tipo) not in tipos:
        return f"tipo {aviso.tipo} no buscado"
    texto = aviso.texto_completo()
    for palabra in b.get("excluir_palabras", []):
        if normalizar(palabra) in texto:
            return f"contiene '{palabra}'"
    barrios = [normalizar(x) for x in ajustes.barrios]
    if barrios and not any(x in normalizar(aviso.barrio) or x in texto for x in barrios):
        return f"barrio '{aviso.barrio}' fuera de zona"
    return ""
