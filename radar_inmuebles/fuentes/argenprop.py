"""Argenprop — HTML plano, sin anti-bot agresivo. La fuente más fácil."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..modelo import construir
from ..util import normalizar, parse_fecha, slug
from .base import Fuente
from .comun import absolutizar, datos_desde_texto, primer_texto, texto_de

BASE = "https://www.argenprop.com"
# Si Argenprop cambia la estructura de URL, editá esto (o ponelo en config.yaml
# como fuentes.argenprop.url_template).
PLANTILLA = "{base}/{tipo}-venta-barrio-{barrio}{ambientes}{pagina}"
RX_FICHA = re.compile(r"/(departamento|ph|casa)[\w-]*--?\d+", re.I)


class Argenprop(Fuente):
    nombre = "argenprop"

    def _url(self, tipo: str, barrio: str, pagina: int) -> str:
        plantilla = self.cfg.get("fuentes.argenprop.url_template") or PLANTILLA
        amb_min = self.cfg.get("busqueda.ambientes_min")
        amb_max = self.cfg.get("busqueda.ambientes_max")
        ambientes = f"-{amb_min}-ambientes" if amb_min and amb_min == amb_max else ""
        return plantilla.format(
            base=BASE, tipo=normalizar(tipo), barrio=slug(barrio),
            ambientes=ambientes,
            pagina=f"-pagina-{pagina}" if pagina > 1 else "",
        )

    def buscar(self, barrio: str) -> list:
        avisos, vistos = [], set()
        for tipo in self.cfg.get("busqueda.tipos", ["departamento"]):
            for pagina in range(1, self.paginas + 1):
                url = self._url(tipo, barrio, pagina)
                html = self.cliente.html(url, referer=BASE)
                if not html:
                    break
                nuevos = self._parsear_listado(html, barrio, tipo)
                nuevos = [a for a in nuevos if a.id not in vistos]
                if not nuevos:
                    break
                vistos.update(a.id for a in nuevos)
                avisos.extend(nuevos)
        return avisos

    # ------------------------------------------------------------------
    def _parsear_listado(self, html: str, barrio: str, tipo: str) -> list:
        sopa = BeautifulSoup(html, "lxml")
        tarjetas = sopa.select("div.listing__item, div[data-item-card], article.listing__item")
        if not tarjetas:
            # Respaldo: cualquier link a una ficha de propiedad.
            tarjetas = [a.find_parent(["div", "article", "li"]) or a
                        for a in sopa.find_all("a", href=RX_FICHA)]

        avisos = []
        for tarjeta in tarjetas:
            try:
                aviso = self._parsear_tarjeta(tarjeta, barrio, tipo)
                if aviso:
                    avisos.append(aviso)
            except Exception as e:                  # noqa: BLE001
                self.log.debug("  tarjeta ilegible: %s", e)
        return avisos

    def _parsear_tarjeta(self, tarjeta, barrio: str, tipo: str):
        enlace = tarjeta if tarjeta.name == "a" else tarjeta.find("a", href=RX_FICHA)
        if not enlace or not enlace.get("href"):
            return None
        href = enlace["href"]
        m = re.search(r"(\d+)(?:\D*)$", href)
        if not m:
            return None
        id_externo = m.group(1)

        texto = texto_de(tarjeta)
        datos = datos_desde_texto(texto)
        if not datos.get("precio"):
            # El precio puede estar en un atributo aparte.
            precio_txt = primer_texto(tarjeta, ".card__price", "[data-price]", ".price")
            datos.update(datos_desde_texto(precio_txt))

        direccion = primer_texto(tarjeta, ".card__address", ".card__title", "h2", "h3")
        titulo = primer_texto(tarjeta, ".card__title", "h2", "h3") or direccion

        return construir(
            self.nombre, id_externo, absolutizar(href, BASE),
            titulo=titulo,
            barrio=barrio,
            direccion=direccion,
            descripcion=texto[:1200],
            tipo="ph" if "ph" in normalizar(titulo + href) else normalizar(tipo),
            imagen=self._imagen(tarjeta),
            **{k: v for k, v in datos.items()
               if k in ("precio", "moneda", "m2_totales", "m2_cubiertos",
                        "ambientes", "dormitorios", "banios", "expensas_ars",
                        "antiguedad")},
        )

    @staticmethod
    def _imagen(tarjeta) -> str | None:
        img = tarjeta.find("img")
        if not img:
            return None
        return img.get("data-src") or img.get("src") or None

    # ------------------------------------------------------------------
    def enriquecer(self, aviso):
        html = self.cliente.html(aviso.url, referer=BASE)
        if not html:
            return aviso
        sopa = BeautifulSoup(html, "lxml")
        desc = primer_texto(sopa, "#verDatosDescripcion", ".section-description--content",
                            "[class*=description]")
        if desc:
            aviso.descripcion = f"{aviso.titulo}\n{desc[:4000]}"
        # "Publicado hace 45 días" / "Publicado el 12/09/2026"
        m = re.search(r"publicad[oa][^.\n]{0,40}", texto_de(sopa).lower())
        if m:
            fecha = parse_fecha(m.group(0))
            if fecha:
                aviso.publicado = fecha
        if not aviso.m2_ref() or not aviso.ambientes:
            aviso_datos = datos_desde_texto(texto_de(sopa.select_one("body")) [:6000])
            aviso.m2_totales = aviso.m2_totales or aviso_datos.get("m2_totales")
            aviso.ambientes = aviso.ambientes or aviso_datos.get("ambientes")
        return aviso
