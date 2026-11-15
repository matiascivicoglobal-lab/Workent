"""Zonaprop — el portal con más stock de CABA, y el más protegido.

Requiere Playwright (fuentes.zonaprop.navegador: true). Primero intenta leer
el JSON que la página deja embebido; si no está, parsea las tarjetas por sus
atributos data-qa, que son más estables que las clases CSS.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..modelo import construir
from ..util import normalizar, parse_fecha, slug
from .base import Fuente
from .comun import (absolutizar, buscar_avisos_json, datos_desde_texto,
                    primer_texto, texto_de, valor_anidado)

BASE = "https://www.zonaprop.com.ar"
PLANTILLA = "{base}/{tipo}-venta-{barrio}{ambientes}{pagina}.html"
ESPERA = "[data-qa='posting PROPERTY'], .postings-container, [data-qa='POSTING_CARD_PRICE']"


def _parece_aviso(d: dict) -> bool:
    claves = set(d)
    return ("postingId" in claves or "posting_id" in claves) and bool(
        {"priceOperationTypes", "price", "operations", "postingLocation"} & claves)


class Zonaprop(Fuente):
    nombre = "zonaprop"
    requiere_navegador = True

    def _url(self, tipo: str, barrio: str, pagina: int) -> str:
        plantilla = self.cfg.get("fuentes.zonaprop.url_template") or PLANTILLA
        amb_min = self.cfg.get("busqueda.ambientes_min")
        amb_max = self.cfg.get("busqueda.ambientes_max")
        ambientes = f"-{amb_min}-ambientes" if amb_min and amb_min == amb_max else ""
        plural = {"departamento": "departamentos", "ph": "ph", "casa": "casas"}
        return plantilla.format(
            base=BASE, tipo=plural.get(normalizar(tipo), normalizar(tipo)),
            barrio=slug(barrio), ambientes=ambientes,
            pagina=f"-pagina-{pagina}" if pagina > 1 else "",
        )

    def buscar(self, barrio: str) -> list:
        if not self.navegador:
            self.log.warning("  zonaprop necesita Playwright; la salteo")
            return []
        avisos, vistos = [], set()
        for tipo in self.cfg.get("busqueda.tipos", ["departamento"]):
            for pagina in range(1, self.paginas + 1):
                html = self.navegador.html(self._url(tipo, barrio, pagina), espera=ESPERA)
                if not html:
                    break
                nuevos = [a for a in self._parsear(html, barrio, tipo)
                          if a.id not in vistos]
                if not nuevos:
                    break
                vistos.update(a.id for a in nuevos)
                avisos.extend(nuevos)
        return avisos

    # ------------------------------------------------------------------
    def _parsear(self, html: str, barrio: str, tipo: str) -> list:
        desde_json = [self._desde_json(d, barrio, tipo)
                      for d in buscar_avisos_json(html, _parece_aviso)]
        desde_json = [a for a in desde_json if a]
        if desde_json:
            self.log.debug("  zonaprop: %d avisos desde JSON embebido", len(desde_json))
            return desde_json
        return self._desde_html(html, barrio, tipo)

    # -- camino 1: JSON embebido ------------------------------------------
    def _desde_json(self, d: dict, barrio: str, tipo: str):
        id_externo = str(valor_anidado(d, "postingId", "posting_id", defecto=""))
        if not id_externo:
            return None

        precio_txt = ""
        ops = d.get("priceOperationTypes") or d.get("operations") or []
        if isinstance(ops, list) and ops:
            precio_txt = str(valor_anidado(ops[0], "prices.amount", "prices.formattedAmount",
                                           "amount", "formattedAmount", defecto=""))
            moneda_txt = str(valor_anidado(ops[0], "prices.currency", "currency",
                                           defecto="USD"))
        else:
            precio_txt, moneda_txt = str(d.get("price", "")), "USD"

        datos = datos_desde_texto(f"{moneda_txt} {precio_txt}")
        caracteristicas = " ".join(
            str(valor_anidado(f, "label", "value", defecto=""))
            for f in (d.get("mainFeatures") or {}).values()
        ) if isinstance(d.get("mainFeatures"), dict) else ""
        datos.update({k: v for k, v in datos_desde_texto(caracteristicas).items()
                      if k not in ("precio", "moneda")})

        url = valor_anidado(d, "url", "postingUrl", defecto=f"/propiedades/{id_externo}.html")
        return construir(
            self.nombre, id_externo, absolutizar(str(url), BASE),
            titulo=str(valor_anidado(d, "postingTitle", "title", defecto=""))[:300],
            barrio=str(valor_anidado(d, "postingLocation.location.name",
                                     "postingLocation.address.name", defecto=barrio)),
            direccion=str(valor_anidado(d, "postingLocation.address.name", defecto="") or ""),
            descripcion=str(valor_anidado(d, "description", "postingDescription",
                                          defecto=""))[:2000],
            publicado=parse_fecha(valor_anidado(d, "publishDate", "createdAt",
                                                "modifiedDate")),
            tipo=normalizar(tipo),
            **{k: v for k, v in datos.items() if k in
               ("precio", "moneda", "m2_totales", "m2_cubiertos", "ambientes",
                "dormitorios", "banios", "expensas_ars")},
        )

    # -- camino 2: DOM con data-qa ----------------------------------------
    def _desde_html(self, html: str, barrio: str, tipo: str) -> list:
        sopa = BeautifulSoup(html, "lxml")
        tarjetas = sopa.select("[data-qa='posting PROPERTY'], div[data-id][data-qa]")
        if not tarjetas:
            tarjetas = [a.find_parent("div") for a in
                        sopa.select("a[href*='/propiedades/']") if a.find_parent("div")]
        avisos = []
        for tarjeta in tarjetas:
            try:
                aviso = self._tarjeta(tarjeta, barrio, tipo)
                if aviso:
                    avisos.append(aviso)
            except Exception as e:                       # noqa: BLE001
                self.log.debug("  tarjeta ilegible: %s", e)
        return avisos

    def _tarjeta(self, tarjeta, barrio: str, tipo: str):
        id_externo = tarjeta.get("data-id") or ""
        enlace = tarjeta.find("a", href=True)
        href = enlace["href"] if enlace else ""
        if not id_externo:
            m = re.search(r"(\d{6,})", href)
            if not m:
                return None
            id_externo = m.group(1)

        precio_txt = primer_texto(tarjeta, "[data-qa='POSTING_CARD_PRICE']", ".price-items")
        expensas_txt = primer_texto(tarjeta, "[data-qa='expensas']")
        features = primer_texto(tarjeta, "[data-qa='POSTING_CARD_FEATURES']", "h3")
        ubicacion = primer_texto(tarjeta, "[data-qa='POSTING_CARD_LOCATION']")
        direccion = primer_texto(tarjeta, "[data-qa='POSTING_CARD_LOCATION'] + div",
                                 ".postingAddress")
        descripcion = primer_texto(tarjeta, "[data-qa='POSTING_CARD_DESCRIPTION']")

        datos = datos_desde_texto(precio_txt)
        datos.update({k: v for k, v in datos_desde_texto(features).items()
                      if k not in ("precio", "moneda")})
        if expensas_txt:
            exp = datos_desde_texto(expensas_txt)
            datos["expensas_ars"] = exp.get("precio")

        return construir(
            self.nombre, id_externo, absolutizar(href, BASE),
            titulo=(descripcion or ubicacion or direccion)[:300],
            barrio=ubicacion or barrio,
            direccion=direccion or None,
            descripcion=f"{descripcion} {texto_de(tarjeta)}"[:1500],
            tipo=normalizar(tipo),
            imagen=_imagen(tarjeta),
            **{k: v for k, v in datos.items() if k in
               ("precio", "moneda", "m2_totales", "m2_cubiertos", "ambientes",
                "dormitorios", "banios", "expensas_ars")},
        )

    # ------------------------------------------------------------------
    def enriquecer(self, aviso):
        if not self.navegador:
            return aviso
        html = self.navegador.html(aviso.url, espera="h1, [data-qa='PROPERTY_DESCRIPTION']",
                                   scroll=False)
        if not html:
            return aviso
        sopa = BeautifulSoup(html, "lxml")
        desc = primer_texto(sopa, "#longDescription", "[data-qa='PROPERTY_DESCRIPTION']",
                            "[class*=description]")
        if desc:
            aviso.descripcion = f"{aviso.titulo}\n{desc[:4000]}"
        texto = texto_de(sopa)[:8000].lower()
        m = re.search(r"publicado\s+hace\s+(\d+)\s*(d[ií]as?|meses|a[nñ]os?)", texto)
        if m:
            fecha = parse_fecha(f"hace {m.group(1)} {m.group(2)}")
            if fecha:
                aviso.publicado = fecha
        return aviso


def _imagen(tarjeta):
    img = tarjeta.find("img")
    if not img:
        return None
    return img.get("data-src") or img.get("src") or None
