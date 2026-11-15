"""Helpers compartidos: parseo tolerante de tarjetas HTML y de JSON embebido.

Los portales cambian clases CSS seguido. En vez de depender de un selector
exacto, leemos el texto de la tarjeta y sacamos los datos con expresiones
regulares; los selectores quedan como atajo cuando funcionan.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Iterator

from ..util import normalizar, parse_numero

RX_PRECIO_USD = re.compile(r"(?:u\$s|us\$|usd|u\$d)\s*([\d.,]+)", re.I)
RX_PRECIO_ARS = re.compile(r"(?:ar\$|\$)\s*([\d.,]+)")
RX_M2 = re.compile(r"([\d.,]+)\s*(?:m2|m²|mts2)")
RX_AMB = re.compile(r"(\d+)\s*amb")
RX_DORM = re.compile(r"(\d+)\s*(?:dorm|hab)")
RX_BANIO = re.compile(r"(\d+)\s*ba[nñ]")
RX_EXPENSAS = re.compile(r"expensas?\s*:?\s*(?:ar)?\$?\s*([\d.,]+)", re.I)
RX_ANTIG = re.compile(r"(\d+)\s*a[nñ]os")


def datos_desde_texto(texto: str) -> dict:
    """Extrae precio, superficie, ambientes, etc. del texto plano de la tarjeta."""
    t = normalizar(texto)
    datos: dict[str, Any] = {}

    m = RX_PRECIO_USD.search(t)
    if m:
        datos["precio"] = parse_numero(m.group(1))
        datos["moneda"] = "USD"
    else:
        m = RX_PRECIO_ARS.search(t)
        if m:
            datos["precio"] = parse_numero(m.group(1))
            datos["moneda"] = "ARS"

    # La tarjeta suele traer "68 m² tot. · 60 m² cub."
    m2s = [parse_numero(x) for x in RX_M2.findall(t)]
    m2s = [v for v in m2s if v and 10 <= v <= 1500]
    if m2s:
        datos["m2_totales"] = max(m2s)
        if len(m2s) > 1:
            datos["m2_cubiertos"] = min(m2s)

    for rx, clave in ((RX_AMB, "ambientes"), (RX_DORM, "dormitorios"),
                      (RX_BANIO, "banios"), (RX_ANTIG, "antiguedad")):
        m = rx.search(t)
        if m:
            datos[clave] = int(m.group(1))

    m = RX_EXPENSAS.search(t)
    if m:
        datos["expensas_ars"] = parse_numero(m.group(1))

    return datos


def texto_de(elemento) -> str:
    """Texto plano de un nodo BeautifulSoup, con separadores."""
    if elemento is None:
        return ""
    return re.sub(r"\s+", " ", elemento.get_text(" ", strip=True))


def primer_texto(elemento, *selectores: str) -> str:
    for sel in selectores:
        nodo = elemento.select_one(sel)
        if nodo:
            t = texto_de(nodo)
            if t:
                return t
    return ""


def absolutizar(href: str, base: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    return base.rstrip("/") + "/" + href.lstrip("/")


# ---------------------------------------------------------------------------
# JSON embebido en la página (Next.js, Nuxt, estados precargados)
# ---------------------------------------------------------------------------

def extraer_json_embebido(html: str) -> Iterator[Any]:
    """Devuelve los blobs JSON que los portales dejan en el HTML."""
    patrones = [
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>',
        r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});?\s*</script>',
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>',
        r'window\.__NUXT__\s*=\s*(\{.*?\});?\s*</script>',
        r'<script[^>]+type="application/json"[^>]*>(\{.*?\})</script>',
    ]
    for patron in patrones:
        for m in re.finditer(patron, html, re.S):
            try:
                yield json.loads(m.group(1))
            except (ValueError, TypeError):
                continue


def recorrer(obj: Any, predicado: Callable[[dict], bool],
             profundidad: int = 0) -> Iterator[dict]:
    """Recorre un árbol JSON y devuelve los dicts que cumplen el predicado."""
    if profundidad > 25:
        return
    if isinstance(obj, dict):
        try:
            if predicado(obj):
                yield obj
                return          # no bajamos dentro de un aviso ya encontrado
        except Exception:       # noqa: BLE001 - predicado defensivo
            pass
        for v in obj.values():
            yield from recorrer(v, predicado, profundidad + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from recorrer(v, predicado, profundidad + 1)


def buscar_avisos_json(html: str, predicado: Callable[[dict], bool]) -> list[dict]:
    vistos: list[dict] = []
    claves = set()
    for blob in extraer_json_embebido(html):
        for d in recorrer(blob, predicado):
            clave = json.dumps(sorted(str(v)[:40] for v in list(d.values())[:6]))
            if clave not in claves:
                claves.add(clave)
                vistos.append(d)
    return vistos


def valor_anidado(d: dict, *caminos: str, defecto=None):
    """valor_anidado(d, 'postingLocation.address.name', 'location.name')"""
    for camino in caminos:
        nodo: Any = d
        ok = True
        for parte in camino.split("."):
            if isinstance(nodo, list) and nodo:
                nodo = nodo[0]
            if isinstance(nodo, dict) and parte in nodo:
                nodo = nodo[parte]
            else:
                ok = False
                break
        if ok and nodo not in (None, "", [], {}):
            return nodo
    return defecto
