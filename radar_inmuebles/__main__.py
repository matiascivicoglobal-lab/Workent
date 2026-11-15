"""CLI del radar.

  python -m radar_inmuebles scan              una pasada completa
  python -m radar_inmuebles watch             queda monitoreando
  python -m radar_inmuebles demo              muestra cómo se ve un aviso (sin red)
  python -m radar_inmuebles verificar         qué fuentes están respondiendo
  python -m radar_inmuebles zonas             valor del m² por barrio
  python -m radar_inmuebles reporte           regenera el HTML desde la base
  python -m radar_inmuebles probar-aviso      manda un mensaje de prueba
      ... --canal telegram                probá otro canal sin tocar la config
  python -m radar_inmuebles login-facebook    abre el navegador para iniciar sesión
  python -m radar_inmuebles telegram-chatid   encuentra tu chat_id y lo guarda
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime

from .ajustes import cargar
from .util import ahora


def _logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# ===========================================================================
def cmd_scan(args, cfg) -> int:
    from .radar import Radar
    from .reporte import generar
    from .sheets_export import exportar

    with Radar(cfg, enviar=not args.sin_enviar, canal=args.canal or '') as radar:
        res = radar.correr()
        refs = radar.tasador.todas(cfg.barrios)
        ruta = generar(res.oportunidades, refs, res.como_dict(), cfg.reporte_html)
        exportar(res.oportunidades, cfg)

    print("\n" + "=" * 54)
    print(f"  Revisados: {res.revisados}   Nuevos: {res.nuevos}   "
          f"Oportunidades: {len(res.oportunidades)}   Enviados: {res.enviados}")
    for fuente, n in res.por_fuente.items():
        print(f"    {fuente:<14} {n:>4} avisos" + ("   ← no respondió" if n == 0 else ""))
    print(f"  Reporte: {ruta}")
    print("=" * 54)
    for ev in res.oportunidades[:10]:
        a = ev.aviso
        print(f"  {ev.puntaje:5.1f}  {a.barrio[:14]:<14} "
              f"USD {a.precio_usd or 0:>9,.0f}  "
              f"{(ev.descuento or 0) * 100:>5.0f}% bajo zona  {a.url}")
    return 0


def cmd_watch(args, cfg) -> int:
    from .radar import Radar
    from .reporte import generar

    intervalo = int(args.cada or cfg.get("monitoreo.intervalo_minutos", 45))
    resumen_activo = bool(cfg.get("alertas.resumen_diario", True))
    hora_resumen = int(cfg.get("alertas.hora_resumen", 20))
    ultimo_resumen = None
    log = logging.getLogger("radar")
    log.info("Monitoreando cada %d minutos. Ctrl+C para cortar.", intervalo)

    while True:
        inicio = time.time()
        try:
            with Radar(cfg, enviar=not args.sin_enviar, canal=args.canal or '') as radar:
                res = radar.correr()
                generar(res.oportunidades, radar.tasador.todas(cfg.barrios),
                        res.como_dict(), cfg.reporte_html)
                hoy = datetime.now().date()
                if (resumen_activo and datetime.now().hour >= hora_resumen
                        and ultimo_resumen != hoy and not args.sin_enviar):
                    radar.enviar_resumen(res)
                    ultimo_resumen = hoy
        except KeyboardInterrupt:
            log.info("Listo, corto acá.")
            return 0
        except Exception as e:                        # noqa: BLE001
            log.error("La corrida falló: %s: %s", type(e).__name__, e, exc_info=args.verbose)

        espera = max(60, intervalo * 60 - (time.time() - inicio))
        log.info("Próxima pasada en %.0f minutos", espera / 60)
        try:
            time.sleep(espera)
        except KeyboardInterrupt:
            log.info("Listo, corto acá.")
            return 0


def cmd_zonas(args, cfg) -> int:
    from .almacen import Almacen
    from .tasacion import Tasador

    with Almacen(cfg.db) as almacen:
        tasador = Tasador(almacen, cfg)
        print(f"\n  Valor de referencia por zona  ({ahora():%d/%m/%Y})")
        print("  " + "-" * 62)
        for barrio in cfg.barrios:
            ref = tasador.referencia(barrio)
            if not ref:
                print(f"  {barrio.title():<16} sin datos todavía")
                continue
            print(f"  {ref.barrio.title():<16} USD {ref.mediana:>7,.0f}/m²   "
                  f"p25 {ref.p25:>6,.0f} · p75 {ref.p75:>6,.0f}   "
                  f"n={ref.n:<4} {ref.origen} ({ref.confianza})")
        r = almacen.resumen()
        print("  " + "-" * 62)
        print(f"  Base: {r['total']} avisos ({r['activos']} activos) — {r['por_barrio']}\n")
    return 0


def cmd_verificar(args, cfg) -> int:
    """Prueba cada fuente con un barrio y reporta si responde."""
    from .fuentes import REGISTRO
    from .navegador import disponible as hay_navegador
    from .notificadores import construir_notificador
    from .red import Cliente

    barrio = cfg.barrios[0] if cfg.barrios else "caballito"
    print(f"\n  Probando cada fuente con '{barrio}'…\n")
    navegador = None
    if hay_navegador() and any(cfg.fuente_usa_navegador(f) for f in cfg.fuentes_activas):
        from .navegador import Navegador
        navegador = Navegador(headless=True).abrir()

    cliente = Cliente(demora=float(cfg.get("scraping.demora_entre_pedidos", 2.5)))
    try:
        for nombre in cfg.fuentes_activas:
            clase = REGISTRO.get(nombre)
            if not clase:
                print(f"  {nombre:<14} ✗  no existe esa fuente")
                continue
            if clase.requiere_navegador and not navegador:
                print(f"  {nombre:<14} —  necesita Playwright (pip install playwright "
                      "&& playwright install chromium)")
                continue
            fuente = clase(cliente, cfg, navegador)
            avisos = fuente.seguro(barrio)
            con_precio = sum(1 for a in avisos if a.precio)
            con_m2 = sum(1 for a in avisos if a.m2_ref())
            estado = "✓" if avisos else "✗"
            print(f"  {nombre:<14} {estado}  {len(avisos):>3} avisos  "
                  f"({con_precio} con precio, {con_m2} con m²)")
            if avisos:
                print(f"                    ej: {avisos[0]}")
    finally:
        cliente.cerrar()
        if navegador:
            navegador.cerrar()

    n = construir_notificador(cfg, canal=args.canal or "")
    listo, falta = n.configurado()
    print(f"\n  Canal de aviso: {n.nombre} {'✓ configurado' if listo else '✗ ' + falta}")
    print(f"  Teléfono destino: {n.e164(str(cfg.get('alertas.telefono', '')))}\n")
    return 0


def cmd_probar_aviso(args, cfg) -> int:
    from .notificadores import construir_notificador

    n = construir_notificador(cfg, canal=args.canal or "")
    listo, falta = n.configurado()
    if not listo:
        print(f"\n  ✗ Canal '{n.nombre}' no configurado:\n    {falta}\n")
        print("  Probá otro canal sin tocar la config, por ejemplo:")
        print("    python -m radar_inmuebles probar-aviso --canal telegram")
        print("    python -m radar_inmuebles probar-aviso --canal whatsapp:twilio\n")
        return 1
    mensaje = (
        "🏠 *Radar Inmuebles conectado*\n"
        "──────────────────\n"
        f"Busco: {', '.join(b.title() for b in cfg.barrios)}\n"
        f"{cfg.get('busqueda.ambientes_min')} ambientes · hasta "
        f"USD {cfg.get('busqueda.precio_usd_max'):,.0f}".replace(",", ".") + "\n"
        f"Te aviso cuando algo esté {cfg.get('oportunidad.descuento_minimo') * 100:.0f}% "
        "o más por debajo del valor del barrio."
    )
    ok = n.enviar(mensaje)
    print(f"\n  ✓ Mensaje enviado por {n.nombre}\n" if ok
          else "\n  ✗ No se pudo enviar (ver el log)\n")
    return 0 if ok else 1


def cmd_reporte(args, cfg) -> int:
    from .almacen import Almacen
    from .reporte import generar
    from .scoring import Evaluador, pasa_filtros_basicos
    from .tasacion import Tasador

    with Almacen(cfg.db) as almacen:
        tasador = Tasador(almacen, cfg)
        ev = Evaluador(tasador, cfg)
        evaluaciones = []
        for barrio in cfg.barrios:
            for a in almacen.avisos(barrio=barrio, dias=90):
                if pasa_filtros_basicos(a, cfg):
                    continue
                e = ev.evaluar(a, baja_precio=almacen.baja_de_precio(a.id))
                if not e.motivo_descarte and (e.descuento or 0) > 0:
                    evaluaciones.append(e)
        ruta = generar(evaluaciones, tasador.todas(cfg.barrios),
                       {"revisados": len(evaluaciones)}, cfg.reporte_html)
    print(f"\n  Reporte generado: {ruta}\n")
    return 0


def cmd_login_facebook(args, cfg) -> int:
    from .navegador import Navegador

    perfil = cfg.ruta_datos("datos/perfil_chromium")
    print("\n  Se abre Chromium. Iniciá sesión en Facebook y después cerrá la ventana.")
    print("  La sesión queda guardada en:", perfil, "\n")
    nav = Navegador(headless=False, perfil=perfil).abrir()
    try:
        pagina = nav._ctx.new_page()
        pagina.goto("https://www.facebook.com/login")
        input("  Cuando termines de iniciar sesión, apretá Enter acá… ")
    finally:
        nav.cerrar()
    print("  Listo. Ya podés poner fuentes.facebook.activa: true en config.yaml\n")
    return 0


def cmd_telegram_chatid(args, cfg) -> int:
    """Encuentra el chat_id escuchando los mensajes que le mandaste al bot."""
    from .ajustes import RAIZ
    from .telegram_alta import chats_del_bot, enmascarar, guardar_en_env

    token = cfg.secreto("TELEGRAM_TOKEN")
    if not token:
        print("\n  ✗ Falta TELEGRAM_TOKEN en radar_inmuebles/.env\n"
              "    Es el token que te dio @BotFather.\n")
        return 1

    print(f"\n  Token: {enmascarar(token)}")
    chats, error = chats_del_bot(token)
    if error:
        print(f"  ✗ {error}\n")
        return 1

    if not chats:
        print("\n  No encontré ningún mensaje todavía.\n"
              "  Abrí Telegram, buscá tu bot y mandale cualquier cosa (un 'hola'),\n"
              "  después volvé a correr este comando.\n"
              "  Ojo: Telegram solo guarda los mensajes 24 horas.\n")
        return 1

    print(f"  Encontré {len(chats)} chat(s):\n")
    for c in chats:
        print(f"    {c['id']:>14}   {c['nombre']}  ({c['tipo']})")

    elegido = chats[0]["id"]
    if len(chats) > 1:
        print(f"\n  Hay más de uno. Uso el primero: {elegido}")
        print("  Si querés otro, poné TELEGRAM_CHAT_ID a mano en el .env.")

    if args.guardar:
        ruta = RAIZ / ".env"
        guardar_en_env(ruta, elegido)
        print(f"\n  ✓ Guardado TELEGRAM_CHAT_ID={elegido} en {ruta}")
        print("    Probalo con: python -m radar_inmuebles probar-aviso --canal telegram\n")
    else:
        print(f"\n  Para guardarlo automáticamente:\n"
              f"    python -m radar_inmuebles telegram-chatid --guardar\n"
              f"  O pegá esto en radar_inmuebles/.env:\n"
              f"    TELEGRAM_CHAT_ID={elegido}\n")
    return 0


def cmd_demo(args, cfg) -> int:
    """Muestra cómo se ve una alerta, sin tocar internet."""
    from .mensajes import alerta
    from .modelo import construir
    from .scoring import Evaluador
    from .tasacion import Referencia
    from datetime import timedelta

    class _TasadorFalso:
        def referencia(self, barrio, ambientes=None):
            return Referencia(barrio, 2250.0, 1980.0, 2600.0, 64, "propia")

    aviso = construir(
        "zonaprop", "51234567",
        "https://www.zonaprop.com.ar/propiedades/ejemplo-51234567.html",
        titulo="Departamento 3 ambientes a reciclar, sobre Av. Rivadavia",
        barrio="Caballito", direccion="Rivadavia al 5200",
        precio=96000, moneda="USD", m2_totales=72, m2_cubiertos=68,
        ambientes=3, dormitorios=2, banios=1, expensas_ars=85000,
        publicado=(ahora() - timedelta(days=96)).isoformat(),
        descripcion=("Departamento en estado original, a reciclar. Dueño directo, "
                     "escucho ofertas. Apto crédito."),
    )
    aviso.precio_usd = 96000.0
    ev = Evaluador(_TasadorFalso(), cfg).evaluar(
        aviso, baja_precio={"desde": 112000, "hasta": 96000, "pct": 0.1428, "dias": 23})

    print("\nAsí te llega el WhatsApp:\n")
    print(alerta(ev))
    print(f"\n[{len(alerta(ev))} caracteres · puntaje {ev.puntaje} · "
          f"alerta={'sí' if Evaluador(_TasadorFalso(), cfg).merece_alerta(ev) else 'no'}]\n")
    return 0


# ===========================================================================
COMANDOS = {
    "scan": cmd_scan,
    "watch": cmd_watch,
    "zonas": cmd_zonas,
    "verificar": cmd_verificar,
    "probar-aviso": cmd_probar_aviso,
    "probar-whatsapp": cmd_probar_aviso,      # alias histórico
    "reporte": cmd_reporte,
    "login-facebook": cmd_login_facebook,
    "telegram-chatid": cmd_telegram_chatid,
    "demo": cmd_demo,
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="radar_inmuebles",
        description="Radar de oportunidades inmobiliarias en CABA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument("comando", choices=sorted(COMANDOS), help="qué hacer")
    p.add_argument("--config", help="ruta a otro config.yaml")
    p.add_argument("--cada", type=int, help="minutos entre pasadas (watch)")
    p.add_argument("--sin-enviar", action="store_true",
                   help="corre todo pero no manda el aviso")
    p.add_argument("--canal",
                   help="pisa alertas.destino: telegram | consola | whatsapp:twilio "
                        "| whatsapp:cloud | whatsapp:callmebot")
    p.add_argument("--guardar", action="store_true",
                   help="telegram-chatid: escribe el chat_id en el .env")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    _logging(args.verbose)
    cfg = cargar(args.config, recargar=True)
    try:
        return COMANDOS[args.comando](args, cfg)
    except KeyboardInterrupt:
        print("\n  Cortado.\n")
        return 130


if __name__ == "__main__":
    sys.exit(main())
