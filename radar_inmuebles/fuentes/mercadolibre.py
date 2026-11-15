"""MercadoLibre Inmuebles, con dos caminos.

1. La API oficial, si hay token. Es la mejor fuente: trae `date_created`,
   así que sabemos hace cuánto está publicado de verdad.
   Token: creá una app en https://developers.mercadolibre.com.ar y poné
   ML_ACCESS_TOKEN en el .env

2. El sitio web, si la API responde 401/403. Desde 2024 MercadoLibre cerró
   la búsqueda pública, así que sin token este es el camino normal. Trae
   menos datos (no siempre la fecha de publicación), pero trae los avisos.

El cambio de un camino al otro es automático.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..modelo import construir
from ..util import normalizar, parse_fecha, slug
from .base import Fuente
from .comun import datos_desde_texto, texto_de

API = "https://api.mercadolibre.com/sites/MLA/search"
CATEGORIA_INMUEBLES = "MLA1459"

WEB = "https://inmuebles.mercadolibre.com.ar"
PLANTILLA_WEB = "{base}/{tipo}/venta/capital-federal/{barrio}/{ambientes}{pagina}"
PLURAL_WEB = {"departamento": "departamentos", "ph": "ph", "casa": "casas"}
RX_ID = re.compile(r"MLA-?(\d{6,})")

# Valores por defecto si falla el autodescubrimiento de filtros.
FALLBACK = {"OPERATION": "242075", "PROPERTY_TYPE": {"departamento": "242060",
                                                     "ph": "242061"}}


class MercadoLibre(Fuente):
    nombre = "mercadolibre"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._filtros: dict | None = None
        self._modo_web = False
        token = self.cfg.secreto("ML_ACCESS_TOKEN")
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}

    # ------------------------------------------------------------------
    def _descubrir_filtros(self) -> dict:
        """Lee available_filters para no hardcodear ids que ML cambia."""
        if self._filtros is not None:
            return self._filtros
        self._filtros = {}
        datos = self.cliente.json(API, params={"category": CATEGORIA_INMUEBLES,
                                               "limit": 1}, headers=self._headers,
                                  reintentar_bloqueos=False)
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
        if self._modo_web:
            return self._buscar_web(barrio)
        avisos = self._buscar_api(barrio)
        if avisos:
            return avisos
        if self.cliente.ultimo_codigo in (401, 403):
            self.log.warning("  la API de MercadoLibre pide token (HTTP %s); "
                             "paso a leer el sitio web",
                             self.cliente.ultimo_codigo)
            self._modo_web = True
            return self._buscar_web(barrio)
        return avisos

    # ------------------------------------------------------------------
    def _buscar_api(self, barrio: str) -> list:
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

                datos = self.cliente.json(API, params=params, headers=self._headers,
                                          reintentar_bloqueos=False)
                if not isinstance(datos, dict):
                    return avisos
                if datos.get("error"):
                    self.log.debug("  ML API: %s", datos.get("message", datos["error"]))
                    return avisos
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

    # ==================================================================
    #  Camino 2: el sitio web
    # ==================================================================
    def _url_web(self, tipo: str, barrio: str, pagina: int) -> str:
        plantilla = self.cfg.get("fuentes.mercadolibre.url_template_web") or PLANTILLA_WEB
        amb_min = self.cfg.get("busqueda.ambientes_min")
        amb_max = self.cfg.get("busqueda.ambientes_max")
        ambientes = f"{amb_min}-ambientes/" if amb_min and amb_min == amb_max else ""
        # MercadoLibre pagina de a 50 con _Desde_51, _Desde_101, ...
        desde = f"_Desde_{pagina * 50 + 1}" if pagina else ""
        return plantilla.format(
            base=WEB, tipo=PLURAL_WEB.get(normalizar(tipo), normalizar(tipo)),
            barrio=slug(barrio), ambientes=ambientes, pagina=desde)

    def _buscar_web(self, barrio: str) -> list:
        avisos, vistos = [], set()
        for tipo in self.cfg.get("busqueda.tipos", ["departamento"]):
            for pagina in range(self.paginas):
                html = self.cliente.html(self._url_web(tipo, barrio, pagina),
                                         referer=WEB)
                if not html:
                    break
                nuevos = [a for a in self._parsear_web(html, barrio, tipo)
                          if a.id not in vistos]
                if not nuevos:
                    break
                vistos.update(a.id for a in nuevos)
                avisos.extend(nuevos)
        return avisos

    def _parsear_web(self, html: str, barrio: str, tipo: str) -> list:
        sopa = BeautifulSoup(html, "lxml")

        # Los selectores se prueban en orden, del contenedor más externo al
        # más interno: si combináramos todos, cada aviso entraría dos veces
        # (una por el <li> y otra por el <div> de adentro).
        tarjetas = []
        for selector in ("li.ui-search-layout__item",
                         "div.ui-search-result__wrapper",
                         "div.poly-card",
                         "div.andes-card"):
            tarjetas = sopa.select(selector)
            if tarjetas:
                break

        if not tarjetas:
            # Respaldo: cualquier link a una publicación MLA.
            for a in sopa.find_all("a", href=RX_ID):
                contenedor = a.find_parent(["li", "div"])
                if contenedor is not None and contenedor not in tarjetas:
                    tarjetas.append(contenedor)

        avisos, vistos = [], set()
        for tarjeta in tarjetas:
            try:
                aviso = self._tarjeta_web(tarjeta, barrio, tipo)
            except Exception as e:                       # noqa: BLE001
                self.log.debug("  tarjeta ilegible: %s", e)
                continue
            # Red de seguridad por si un selector igual anida.
            if aviso and aviso.id_externo not in vistos:
                vistos.add(aviso.id_externo)
                avisos.append(aviso)
        return avisos

    def _tarjeta_web(self, tarjeta, barrio: str, tipo: str):
        enlace = tarjeta if tarjeta.name == "a" else tarjeta.find("a", href=RX_ID)
        if not enlace or not enlace.get("href"):
            return None
        m = RX_ID.search(enlace["href"])
        if not m:
            return None
        id_externo = f"MLA{m.group(1)}"

        texto = texto_de(tarjeta)
        datos = datos_desde_texto(texto)
        if not datos.get("precio"):
            return None

        titulo = texto_de(tarjeta.select_one(
            "a.poly-component__title, h2, h3, .ui-search-item__title")) or texto[:120]
        ubicacion = texto_de(tarjeta.select_one(
            ".poly-component__location, .ui-search-item__location")) or barrio

        # MercadoLibre mezcla barrios: descartamos lo que no sea de la zona.
        if normalizar(barrio) not in normalizar(f"{ubicacion} {titulo}"):
            return None

        imagen = None
        img = tarjeta.find("img")
        if img:
            imagen = img.get("data-src") or img.get("src")

        return construir(
            self.nombre, id_externo, enlace["href"].split("#")[0].split("?")[0],
            titulo=titulo[:300],
            barrio=ubicacion or barrio,
            direccion=ubicacion or None,
            descripcion=texto[:1500],
            tipo="ph" if "ph" in normalizar(titulo) else normalizar(tipo),
            imagen=imagen,
            **{k: v for k, v in datos.items() if k in
               ("precio", "moneda", "m2_totales", "m2_cubiertos", "ambientes",
                "dormitorios", "banios", "expensas_ars")},
        )

    # ------------------------------------------------------------------
    def enriquecer(self, aviso):
        """Trae la descripción larga: ahí están 'a reciclar', 'dueño directo', etc."""
        if not self._modo_web:
            url = f"https://api.mercadolibre.com/items/{aviso.id_externo}/description"
            datos = self.cliente.json(url, headers=self._headers,
                                      reintentar_bloqueos=False)
            if isinstance(datos, dict) and datos.get("plain_text"):
                aviso.descripcion = f"{aviso.titulo}\n{datos['plain_text'][:4000]}"
                return aviso

        html = self.cliente.html(aviso.url, referer=WEB)
        if not html:
            return aviso
        sopa = BeautifulSoup(html, "lxml")
        desc = texto_de(sopa.select_one(
            ".ui-pdp-description__content, [data-testid='content'], #description"))
        if desc:
            aviso.descripcion = f"{aviso.titulo}\n{desc[:4000]}"
        if not aviso.m2_ref() or not aviso.ambientes:
            ficha = texto_de(sopa.select_one(
                ".ui-pdp-specs, .ui-vpp-highlighted-specs, .ui-pdp-container"))
            extra = datos_desde_texto(ficha[:4000])
            aviso.m2_totales = aviso.m2_totales or extra.get("m2_totales")
            aviso.ambientes = aviso.ambientes or extra.get("ambientes")
        return aviso
