"""Reporte HTML local con el ranking completo de oportunidades."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

PLANTILLA = """<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar Inmuebles</title>
<style>
:root{{--bg:#fbfaf8;--fg:#1b1a17;--suave:#6b6761;--linea:#e6e2dc;--tarjeta:#fff;
--verde:#1f7a4d;--rojo:#b3261e;--ambar:#9a6700;}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#16150f;
--fg:#f0ede6;--suave:#a39e94;--linea:#2e2c25;--tarjeta:#1f1e18;--verde:#5fd39a;
--rojo:#ff8a80;--ambar:#e3b341;}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
padding:24px 16px 64px}}
.wrap{{max-width:980px;margin:0 auto}}
h1{{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}}
.sub{{color:var(--suave);font-size:13px;margin-bottom:24px}}
.zonas{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:28px}}
.zona{{background:var(--tarjeta);border:1px solid var(--linea);border-radius:10px;
padding:10px 14px;min-width:150px}}
.zona b{{display:block;font-size:19px}}
.zona span{{color:var(--suave);font-size:12px}}
.aviso{{background:var(--tarjeta);border:1px solid var(--linea);border-radius:12px;
padding:16px;margin-bottom:12px;display:grid;grid-template-columns:76px 1fr;gap:16px}}
.pts{{font-size:26px;font-weight:650;text-align:center;line-height:1}}
.pts small{{display:block;font-size:11px;color:var(--suave);font-weight:400;margin-top:4px}}
.tit{{font-weight:600;margin-bottom:2px}}
.tit a{{color:inherit;text-decoration:none}}
.tit a:hover{{text-decoration:underline}}
.meta{{color:var(--suave);font-size:13px;margin-bottom:8px}}
.datos{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{font-size:12px;border:1px solid var(--linea);border-radius:999px;padding:2px 9px}}
.bueno{{color:var(--verde);border-color:currentColor}}
.malo{{color:var(--rojo);border-color:currentColor}}
.ojo{{color:var(--ambar);border-color:currentColor}}
.vacio{{color:var(--suave);padding:40px 0;text-align:center}}
footer{{color:var(--suave);font-size:12px;margin-top:32px;border-top:1px solid var(--linea);
padding-top:12px}}
@media(max-width:560px){{.aviso{{grid-template-columns:1fr}}.pts{{text-align:left}}}}
</style></head><body><div class="wrap">
<h1>Radar Inmuebles</h1>
<div class="sub">{sub}</div>
<div class="zonas">{zonas}</div>
{avisos}
<footer>{pie}</footer>
</div></body></html>"""


def _usd(v) -> str:
    return f"USD {v:,.0f}".replace(",", ".") if v else "s/d"


def _esc(t) -> str:
    return html.escape(str(t or ""))


def generar(evaluaciones, referencias, stats: dict, destino: Path) -> Path:
    zonas = "".join(
        f'<div class="zona"><span>{_esc(r.barrio.title())}</span>'
        f'<b>{_usd(r.mediana)}/m²</b>'
        f'<span>n={r.n} · {r.origen} · confianza {r.confianza}</span></div>'
        for r in referencias) or '<div class="zona"><span>Sin referencias todavía</span></div>'

    filas = []
    for ev in sorted(evaluaciones, key=lambda e: e.puntaje, reverse=True):
        a = ev.aviso
        m2 = a.m2_ref()
        chips = []
        if ev.descuento is not None:
            # "33% bajo zona" se entiende al toque; "+33%" se lee como más caro.
            if ev.descuento >= 0:
                chips.append(f'<span class="chip bueno">'
                             f'{ev.descuento * 100:.0f}% bajo zona</span>')
            else:
                chips.append(f'<span class="chip malo">'
                             f'{-ev.descuento * 100:.0f}% sobre zona</span>')
        if ev.precio_m2:
            chips.append(f'<span class="chip">{_usd(ev.precio_m2)}/m²</span>')
        if ev.margen:
            clase = "bueno" if ev.margen > 0 else "malo"
            chips.append(f'<span class="chip {clase}">margen {_usd(ev.margen)} '
                         f'({ev.margen_pct * 100:+.0f}%)</span>')
        if ev.dias_publicado is not None:
            chips.append(f'<span class="chip">{ev.dias_publicado} días publicado</span>')
        if ev.baja_precio:
            chips.append(f'<span class="chip bueno">bajó '
                         f'{ev.baja_precio["pct"] * 100:.0f}%</span>')
        for s in ev.senales[:3]:
            chips.append(f'<span class="chip">{_esc(s)}</span>')
        for r in ev.riesgos[:2]:
            chips.append(f'<span class="chip malo">{_esc(r)}</span>')
        if ev.sospechoso:
            chips.append('<span class="chip ojo">verificar: muy barato</span>')

        filas.append(f"""<div class="aviso">
<div class="pts">{ev.puntaje:.0f}<small>puntaje</small></div>
<div>
<div class="tit"><a href="{_esc(a.url)}" target="_blank" rel="noopener">
{_esc(a.titulo[:110] or a.direccion or a.id)}</a></div>
<div class="meta">{_esc(a.barrio.title())} · {a.ambientes or '?'} amb ·
{f'{m2:.0f} m²' if m2 else 's/m²'} · <b>{_usd(a.precio_usd)}</b> · {_esc(a.fuente)}</div>
<div class="datos">{''.join(chips)}</div>
</div></div>""")

    cuerpo = "".join(filas) or '<div class="vacio">Todavía no hay nada que pase el filtro.</div>'
    sub = (f"{stats.get('revisados', 0)} avisos revisados · "
           f"{stats.get('nuevos', 0)} nuevos · {len(evaluaciones)} en el ranking")
    pie = ("Los valores de zona son medianas de avisos publicados (precio de "
           "oferta, no de cierre: la venta real suele cerrar 5-10% abajo). "
           f"Generado el {datetime.now():%d/%m/%Y %H:%M}.")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(PLANTILLA.format(sub=_esc(sub), zonas=zonas, avisos=cuerpo,
                                        pie=_esc(pie)), encoding="utf-8")
    return destino
