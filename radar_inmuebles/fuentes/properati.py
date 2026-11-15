"""Properati — Next.js: los avisos vienen en el JSON embebido del HTML."""

from __future__ import annotations

import re

from ..modelo import construir
from ..util import normalizar, parse_fecha, slug
from .base import Fuente
from .comun import (absolutizar, buscar_avisos_json, datos_desde_texto,
                    valor_anidado)

BASE = "https://www.properati.com.ar"
PLANTILLA = "{base}/s/{barrio}-capital-federal/{tipo}/venta{query}"


def _parece_aviso(d: dict) -> bool:
    claves = set(d)
    tiene_precio = bool({"price", "priceUsd", "price_usd", "listing_price"} & claves)
    tiene_id = bool({"id", "listingId", "listing_id", "slug", "uuid"} & claves)
    tiene_sup = bool({"surface", "surface_total", "surfaceTotal", "area",
                      "surface_covered"} & claves)
    return tiene_precio and tiene_id and (tiene_sup or "property_type" in claves
                                          or "propertyType" in claves)


class Properati(Fuente):
    nombre = "properati"

    def _url(self, tipo: str, barrio: str, pagina: int) -> str:
        plantilla = self.cfg.get("fuentes.properati.url_template") or PLANTILLA
        partes = []
        amb = self.cfg.get("busqueda.ambientes_min")
        if amb:
            partes.append(f"habitaciones={amb}")
        if pagina > 1:
            partes.append(f"page={pagina}")
        query = "?" + "&".join(partes) if partes else ""
        return plantilla.format(base=BASE, barrio=slug(barrio),
                                tipo=normalizar(tipo), query=query)

    def buscar(self, barrio: str) -> list:
        avisos, vistos = [], set()
        for tipo in self.cfg.get("busqueda.tipos", ["departamento"]):
            for pagina in range(1, self.paginas + 1):
                html = self.cliente.html(self._url(tipo, barrio, pagina), referer=BASE)
                if not html:
                    break
                crudos = buscar_avisos_json(html, _parece_aviso)
                nuevos = []
                for crudo in crudos:
                    aviso = self._parsear(crudo, barrio, tipo)
                    if aviso and aviso.id not in vistos:
                        vistos.add(aviso.id)
                        nuevos.append(aviso)
                if not nuevos:
                    break
                avisos.extend(nuevos)
        return avisos

    # ------------------------------------------------------------------
    def _parsear(self, d: dict, barrio: str, tipo: str):
        id_externo = str(valor_anidado(d, "id", "listingId", "listing_id", "uuid",
                                       defecto="") or "")
        if not id_externo:
            return None

        precio = valor_anidado(d, "price", "priceUsd", "price_usd", "listing_price")
        if isinstance(precio, dict):
            moneda = precio.get("currency")
            precio = precio.get("amount") or precio.get("value")
        else:
            moneda = valor_anidado(d, "currency", "price_currency", "currency_id")
        moneda = "USD" if normalizar(str(moneda)) in ("usd", "u$s", "dolar", "dolares") else \
                 ("ARS" if moneda else None)

        url = valor_anidado(d, "url", "permalink", "link", "slug", defecto="")
        if url and not str(url).startswith("http"):
            url = absolutizar(f"/detalle/{url}" if "/" not in str(url) else str(url), BASE)

        texto = " ".join(str(valor_anidado(d, c, defecto="")) for c in
                         ("title", "description", "short_description", "name"))
        extras = datos_desde_texto(texto)

        return construir(
            self.nombre, id_externo, url or f"{BASE}/detalle/{id_externo}",
            titulo=str(valor_anidado(d, "title", "name", defecto=""))[:300],
            barrio=str(valor_anidado(d, "neighborhood", "location.name",
                                     "location_name", defecto=barrio)),
            direccion=valor_anidado(d, "address", "location.address"),
            precio=precio,
            moneda=moneda,
            m2_totales=valor_anidado(d, "surface_total", "surfaceTotal", "surface",
                                     "area") or extras.get("m2_totales"),
            m2_cubiertos=valor_anidado(d, "surface_covered", "surfaceCovered",
                                       "covered_area"),
            ambientes=valor_anidado(d, "rooms", "ambientes", "total_rooms")
                      or extras.get("ambientes"),
            dormitorios=valor_anidado(d, "bedrooms", "habitaciones", "dormitorios"),
            banios=valor_anidado(d, "bathrooms", "banos"),
            publicado=parse_fecha(valor_anidado(d, "created_at", "createdAt",
                                                "published_at", "date")),
            imagen=_primera_imagen(d),
            descripcion=texto[:2000],
            tipo=normalizar(str(valor_anidado(d, "property_type", "propertyType",
                                              defecto=tipo))),
        )


def _primera_imagen(d: dict):
    imgs = valor_anidado(d, "images", "photos", "pictures", "thumbnail")
    if isinstance(imgs, str):
        return imgs
    if isinstance(imgs, list) and imgs:
        primera = imgs[0]
        if isinstance(primera, str):
            return primera
        if isinstance(primera, dict):
            return primera.get("url") or primera.get("src")
    return None
