"""MercadoLibre Inmuebles — vía API pública oficial.

Es la fuente más estable: no hay HTML que se rompa y trae `date_created`,
así que sabemos hace cuánto está publicado de verdad.

Si la API empieza a pedir token: creá una app en
https://developers.mercadolibre.com.ar y poné ML_ACCESS_TOKEN en el .env
"""

from __future__ import annotations

from ..modelo import construir
from ..util import normalizar, parse_fecha
from .base import Fuente

API = "https://api.mercadolibre.com/sites/MLA/search"
CATEGORIA_INMUEBLES = "MLA1459"

# Valores por defecto si falla el autodescubrimiento de filtros.
FALLBACK = {"OPERATION": "242075", "PROPERTY_TYPE": {"departamento": "242060",
                                                     "ph": "242061"}}


class MercadoLibre(Fuente):
    nombre = "mercadolibre"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._filtros: dict | None = None
        token = self.cfg.secreto("ML_ACCESS_TOKEN")
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}

    # ------------------------------------------------------------------
    def _descubrir_filtros(self) -> dict:
        """Lee available_filters para no hardcodear ids que ML cambia."""
        if self._filtros is not None:
            return self._filtros
        self._filtros = {}
        datos = self.cliente.json(API, params={"category": CATEGORIA_INMUEBLES,
                                               "limit": 1}, headers=self._headers)
        if not isinstance(datos, dict):
            self.log.debug("  no pude descubrir filtros, uso los de respaldo")
            return self._filtros
        for f in datos.get("available_filters", []):
            fid = f.get("id")
            if fid in ("OPERATION", "PROPERTY_TYPE"):
                self._filtros[fid] = {normalizar(v.get("name")): str(v.get("id"))
                                      for v in f.get("values", [])}
        return self._filtros

    def _id_filtro(self, filtro: str, nombre: str) -> str | None:
        valores = self._descubrir_filtros().get(filtro, {})
        n = normalizar(nombre)
        for clave, vid in valores.items():
            if clave == n or n in clave:
                return vid
        if filtro == "OPERATION":
            return FALLBACK["OPERATION"]
        return FALLBACK["PROPERTY_TYPE"].get(n)

    # ------------------------------------------------------------------
    def buscar(self, barrio: str) -> list:
        avisos = []
        operacion = self._id_filtro("OPERATION", self.cfg.get("busqueda.operacion", "venta"))
        for tipo in self.cfg.get("busqueda.tipos", ["departamento"]):
            tipo_id = self._id_filtro("PROPERTY_TYPE", tipo)
            for pagina in range(self.paginas):
                params = {
                    "category": CATEGORIA_INMUEBLES,
                    "q": f"{tipo} {barrio} capital federal",
                    "limit": 50,
                    "offset": pagina * 50,
                    "sort": "date_desc",
                }
                if operacion:
                    params["OPERATION"] = operacion
                if tipo_id:
                    params["PROPERTY_TYPE"] = tipo_id

                datos = self.cliente.json(API, params=params, headers=self._headers)
                if not isinstance(datos, dict):
                    break
                if datos.get("error"):
                    self.log.warning("  ML: %s — ¿falta ML_ACCESS_TOKEN en el .env?",
                                     datos.get("message", datos["error"]))
                    break
                resultados = datos.get("results", [])
                if not resultados:
                    break
                for r in resultados:
                    aviso = self._parsear(r, barrio, tipo)
                    if aviso:
                        avisos.append(aviso)
                if len(resultados) < 50:
                    break
        return avisos

    # ------------------------------------------------------------------
    def _parsear(self, r: dict, barrio_buscado: str, tipo: str):
        attrs = {a.get("id"): a for a in r.get("attributes", []) if a.get("id")}

        def num(clave):
            a = attrs.get(clave)
            if not a:
                return None
            struct = a.get("value_struct") or {}
            return struct.get("number") if struct.get("number") is not None else a.get("value_name")

        ubic = r.get("location") or r.get("seller_address") or {}
        barrio = ((ubic.get("neighborhood") or {}).get("name")
                  or (ubic.get("city") or {}).get("name") or barrio_buscado)

        # ML a veces devuelve cosas de otros barrios con el mismo `q`.
        if normalizar(barrio_buscado) not in normalizar(f"{barrio} {r.get('title','')}"):
            direccion = (ubic.get("address_line") or "")
            if normalizar(barrio_buscado) not in normalizar(direccion):
                return None

        return construir(
            self.nombre, r.get("id"), r.get("permalink", ""),
            titulo=r.get("title", ""),
            barrio=barrio,
            direccion=ubic.get("address_line"),
            precio=r.get("price"),
            moneda="USD" if r.get("currency_id") == "USD" else "ARS",
            m2_totales=num("TOTAL_AREA"),
            m2_cubiertos=num("COVERED_AREA"),
            ambientes=num("ROOMS"),
            dormitorios=num("BEDROOMS"),
            banios=num("FULL_BATHROOMS"),
            antiguedad=num("PROPERTY_AGE"),
            expensas_ars=num("MAINTENANCE_FEE"),
            publicado=parse_fecha(r.get("date_created") or r.get("start_time")),
            imagen=r.get("thumbnail", "").replace("-I.jpg", "-O.jpg"),
            descripcion=r.get("title", ""),
            tipo=normalizar(tipo),
            extra={"condicion": r.get("condition"), "vendedor": (r.get("seller") or {}).get("id")},
        )

    # ------------------------------------------------------------------
    def enriquecer(self, aviso):
        """Trae la descripción larga: ahí están 'a reciclar', 'dueño directo', etc."""
        url = f"https://api.mercadolibre.com/items/{aviso.id_externo}/description"
        datos = self.cliente.json(url, headers=self._headers)
        if isinstance(datos, dict) and datos.get("plain_text"):
            aviso.descripcion = f"{aviso.titulo}\n{datos['plain_text'][:4000]}"
        return aviso
