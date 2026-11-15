"""Armado de los mensajes de WhatsApp.

WhatsApp usa *negrita*, _cursiva_ y ~tachado~. No hay tablas ni links con
texto: el link va pelado al final para que sea tocable.
"""

from __future__ import annotations

from .util import normalizar

BARRA = "─" * 18


def _usd(v: float | None) -> str:
    if v is None:
        return "s/d"
    return f"USD {v:,.0f}".replace(",", ".")


def _pct(v: float | None, signo: bool = True) -> str:
    if v is None:
        return "s/d"
    s = "+" if (signo and v > 0) else ""
    return f"{s}{v * 100:.0f}%"


def _antiguedad(dias: int | None) -> str:
    if dias is None:
        return "fecha no publicada"
    if dias == 0:
        return "publicado hoy"
    if dias == 1:
        return "publicado ayer"
    if dias < 30:
        return f"publicado hace {dias} días"
    meses = dias // 30
    return f"publicado hace {meses} {'mes' if meses == 1 else 'meses'}"


def alerta(ev, tipo: str = "nueva") -> str:
    """Mensaje de una oportunidad. Pensado para leerse en 5 segundos."""
    a = ev.aviso
    ref = ev.referencia
    m2 = a.m2_ref()

    encabezado = "🔥 *OPORTUNIDAD*" if ev.puntaje >= 75 else "🏠 *Posible oportunidad*"
    if tipo == "baja_precio":
        encabezado = "📉 *BAJÓ DE PRECIO*"

    lineas = [
        f"{encabezado}  ·  {ev.puntaje:.0f}/100",
        f"*{a.barrio.title()}* · {a.ambientes or '?'} amb · {m2:.0f} m²" if m2
        else f"*{a.barrio.title()}* · {a.ambientes or '?'} amb",
        f"*{_usd(a.precio_usd)}*" + (f"  ({_usd(a.precio_usd / m2)}/m²)" if m2 else ""),
        BARRA,
    ]

    # --- el corazón del aviso: por qué es oportunidad ---------------------
    if ref and ev.precio_m2:
        lineas.append(
            f"📊 La zona está en *{_usd(ref.mediana)}/m²* "
            f"y esta en *{_usd(ev.precio_m2)}/m²*"
        )
        lineas.append(f"👉 *{_pct(ev.descuento, signo=False)} más barata* que la mediana del barrio")
        if ref.origen == "semilla":
            lineas.append("   _(referencia estimada: el radar aún junta muestra)_")
        else:
            lineas.append(f"   _(sobre {ref.n} avisos comparables · confianza {ref.confianza})_")

    if ev.baja_precio:
        b = ev.baja_precio
        lineas.append(f"📉 Bajó {_pct(b['pct'], signo=False)} "
                      f"({_usd(b['desde'])} → {_usd(b['hasta'])}) en {b['dias']} días")

    lineas.append(f"📅 {_antiguedad(ev.dias_publicado).capitalize()}")

    # --- la cuenta del reciclado -----------------------------------------
    if ev.margen:
        lineas += [
            BARRA,
            "*Si la reciclás:*",
            f"🔨 Obra estimada: {_usd(ev.costo_reforma)}",
            f"💰 Inversión total: {_usd(ev.inversion_total)}",
            f"🏷️ Valor reciclada: {_usd(ev.valor_objetivo)}",
            f"📈 Margen neto de comisión: *{_usd(ev.margen)}* ({_pct(ev.margen_pct)})",
        ]

    if ev.senales:
        lineas += [BARRA, "🔎 " + " · ".join(ev.senales[:4])]
    if ev.riesgos:
        lineas.append("⚠️ Ojo: " + " · ".join(ev.riesgos[:3]))
    if ev.sospechoso:
        lineas.append("⚠️ *Precio muy por debajo del mercado.* Puede ser error de "
                      "carga, cochera/lote mal clasificado o una traba legal. Verificá "
                      "antes de entusiasmarte.")
    if a.expensas_ars:
        lineas.append(f"🧾 Expensas: ${a.expensas_ars:,.0f}".replace(",", "."))

    lineas += [BARRA, f"📍 {a.direccion or a.titulo[:70]}", f"🔗 {a.url}",
               f"_vía {a.fuente}_"]
    return "\n".join(lineas)


def resumen_diario(evaluaciones, referencias, stats: dict) -> str:
    """Un solo mensaje por día con el estado del radar."""
    lineas = ["📋 *Resumen del radar*", BARRA]

    if referencias:
        lineas.append("*Valor de la zona hoy (USD/m²):*")
        for r in referencias:
            marca = "" if r.origen != "semilla" else " ~est~"
            lineas.append(f"• {r.barrio.title()}: {_usd(r.mediana)}{marca} "
                          f"_(n={r.n})_")
        lineas.append(BARRA)

    lineas.append(f"🔍 {stats.get('revisados', 0)} avisos revisados · "
                  f"{stats.get('nuevos', 0)} nuevos · "
                  f"{stats.get('oportunidades', 0)} oportunidades")

    top = sorted(evaluaciones, key=lambda e: e.puntaje, reverse=True)[:5]
    if top:
        lineas += [BARRA, "*Mejores de hoy:*"]
        for ev in top:
            a = ev.aviso
            lineas.append(
                f"{ev.puntaje:.0f} · {a.barrio.title()} · {_usd(a.precio_usd)} · "
                f"{_pct(ev.descuento, signo=False) if ev.descuento else ''} bajo zona"
            )
            lineas.append(f"   {a.url}")
    else:
        lineas.append("\nHoy no apareció nada que pase el filtro. "
                      "Seguimos mirando.")
    return "\n".join(lineas)


def error(texto: str) -> str:
    return f"⚠️ *Radar con problemas*\n{BARRA}\n{texto}"


def recortar(mensaje: str, limite: int = 3500) -> str:
    """WhatsApp corta los mensajes muy largos."""
    if len(mensaje) <= limite:
        return mensaje
    return mensaje[:limite - 20].rsplit("\n", 1)[0] + "\n…"
