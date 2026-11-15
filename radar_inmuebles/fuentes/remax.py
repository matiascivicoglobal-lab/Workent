"""RE/MAX Argentina — API JSON pública que usa su propio sitio.

Es la red con más propiedades de dueños que quieren vender rápido.
Si cambian el contrato de la API, esta fuente devuelve 0 sin romper nada:
revisalo con `python -m radar_inmuebles verificar`.
"""

from __future__ import annotations

from ..modelo import construir
from ..util import normalizar, parse_fecha
from .base import Fuente
from .comun import valor_anidado

API = "https://api.remax.com.ar/api/v1/listings/findAll"
WEB = "https://www.remax.com.ar"

OPERACION_VENTA = 1
TIPO = {"departamento": 1, "casa": 2, "ph": 3}


class Remax(Fuente):
    nombre = "remax"

    def buscar(self, barrio: str) -> list:
        avisos = []
        amb_min = self.cfg.get("busqueda.ambientes_min")
        amb_max = self.cfg.get("busqueda.ambientes_max")
        for pagina in range(self.paginas):
            params = {
                "page": pagina,
                "pageSize": 50,
                "sort": "-createdAt",
                "in:operationId": OPERACION_VENTA,
                "in:typeId": ",".join(
                    str(TIPO[t]) for t in self.cfg.get("busqueda.tipos", [])
                    if t in TIPO) or "1",
                "locations": f"in::::{barrio}::",
                "filterCount": 0,
            }
            if amb_min:
                params["min:totalRooms"] = amb_min
            if amb_max:
                params["max:totalRooms"] = amb_max

            datos = self.cliente.json(API, params=params, referer=WEB)
            if not isinstance(datos, dict):
                break
            items = datos.get("data") or datos.get("results") or []
            if not items:
                break
            for item in items:
                aviso = self._parsear(item, barrio)
                if aviso:
                    avisos.append(aviso)
            if len(items) < 50:
                break
        return avisos

    def _parsear(self, d: dict, barrio: str):
        id_externo = str(valor_anidado(d, "id", "slug", defecto=""))
        if not id_externo:
            return None
        moneda = normalizar(str(valor_anidado(d, "currency.value", "currency",
                                              defecto="USD")))
        ubic = " ".join(str(valor_anidado(d, c, defecto="")) for c in
                        ("geoLabel", "displayAddress", "address"))
        if normalizar(barrio) not in normalizar(ubic):
            ubic = f"{ubic} {barrio}"

        return construir(
            self.nombre, id_externo,
            f"{WEB}/listings/{valor_anidado(d, 'slug', defecto=id_externo)}",
            titulo=str(valor_anidado(d, "title", "displayAddress", defecto=""))[:300],
            barrio=str(valor_anidado(d, "geoLabel", defecto=barrio)),
            direccion=valor_anidado(d, "displayAddress", "address"),
            precio=valor_anidado(d, "price", "priceUsd"),
            moneda="USD" if "usd" in moneda or "dol" in moneda else "ARS",
            m2_totales=valor_anidado(d, "dimensionTotalBuilt", "totalSurface",
                                     "dimensionLand"),
            m2_cubiertos=valor_anidado(d, "dimensionCovered", "coveredSurface"),
            ambientes=valor_anidado(d, "totalRooms", "rooms"),
            dormitorios=valor_anidado(d, "bedrooms"),
            banios=valor_anidado(d, "bathrooms"),
            expensas_ars=valor_anidado(d, "expenses"),
            publicado=parse_fecha(valor_anidado(d, "createdAt", "publishedAt")),
            descripcion=str(valor_anidado(d, "description", defecto=""))[:2000],
            imagen=valor_anidado(d, "photos.value", "photos.url", "mainPhoto"),
            tipo=normalizar(str(valor_anidado(d, "type.value", defecto="departamento"))),
        )
