"""Facebook Marketplace — opcional, apagado por defecto.

LEÉ ESTO ANTES DE ACTIVARLO
---------------------------
Marketplace no tiene API pública para esto. La única forma es abrir el sitio
con tu propia sesión iniciada. Eso implica:
  * Las Condiciones de Facebook prohíben el acceso automatizado. Si lo usás
    muy seguido podés comerte un bloqueo temporal o permanente de tu cuenta.
  * Nunca pongas tu usuario y contraseña acá. Se usa un perfil de Chromium
    persistente: iniciás sesión UNA vez a mano y queda guardado.
        python -m radar_inmuebles login-facebook
  * Dejá `intervalo_minutos` alto (>= 60) para esta fuente.

Alternativa sin riesgo: creá la búsqueda en Marketplace desde tu celular y
activá las notificaciones de "nuevas publicaciones". No te da el análisis de
precio por m², pero no arriesga la cuenta.
"""

from __future__ import annotations

import json
import re

from ..modelo import construir
from ..util import ahora, normalizar
from .base import Fuente
from .comun import datos_desde_texto

BASE = "https://www.facebook.com"
BUSQUEDA = (BASE + "/marketplace/category/propertyforsale/"
            "?query={consulta}&exact=false&sortBy=creation_time_descend")

RX_ITEM = re.compile(r'"marketplace_listing_title":"(.*?)"', re.S)
RX_BLOQUE = re.compile(
    r'\{"__typename":"GroupCommerceProductItem".*?"id":"(\d+)".*?'
    r'"marketplace_listing_title":"(.*?)".*?'
    r'"formatted_amount":"(.*?)".*?\}', re.S)


class Facebook(Fuente):
    nombre = "facebook"
    requiere_navegador = True

    def buscar(self, barrio: str) -> list:
        if not self.navegador:
            self.log.warning("  facebook necesita Playwright con sesión iniciada")
            return []
        consulta = f"departamento {barrio}".replace(" ", "%20")
        html = self.navegador.html(BUSQUEDA.format(consulta=consulta),
                                   espera="[aria-label*='Marketplace'], div[role='main']")
        if not html:
            return []
        if "login" in html[:3000].lower() and "marketplace" not in html[:3000].lower():
            self.log.warning("  facebook: sesión no iniciada. Corré "
                             "'python -m radar_inmuebles login-facebook'")
            return []
        return self._parsear(html, barrio)

    # ------------------------------------------------------------------
    def _parsear(self, html: str, barrio: str) -> list:
        avisos, vistos = [], set()
        for m in RX_BLOQUE.finditer(html):
            id_externo, titulo, precio_txt = m.groups()
            if id_externo in vistos:
                continue
            vistos.add(id_externo)
            aviso = self._armar(id_externo, _desescapar(titulo),
                                _desescapar(precio_txt), barrio)
            if aviso:
                avisos.append(aviso)

        if not avisos:
            # Respaldo: links de item + título suelto.
            for m in re.finditer(r'/marketplace/item/(\d+)', html):
                id_externo = m.group(1)
                if id_externo in vistos:
                    continue
                vistos.add(id_externo)
                ventana = html[m.start():m.start() + 1500]
                titulos = RX_ITEM.findall(ventana)
                titulo = _desescapar(titulos[0]) if titulos else ""
                precio = re.search(r'"formatted_amount":"(.*?)"', ventana)
                aviso = self._armar(id_externo, titulo,
                                    _desescapar(precio.group(1)) if precio else "",
                                    barrio)
                if aviso:
                    avisos.append(aviso)
        return avisos

    def _armar(self, id_externo: str, titulo: str, precio_txt: str, barrio: str):
        texto = f"{titulo} {precio_txt}"
        datos = datos_desde_texto(texto)
        if not datos.get("precio"):
            return None
        return construir(
            self.nombre, id_externo, f"{BASE}/marketplace/item/{id_externo}",
            titulo=titulo[:300],
            barrio=barrio,
            descripcion=titulo,
            publicado=ahora(),          # Marketplace ordenado por más reciente
            tipo="ph" if "ph" in normalizar(titulo) else "departamento",
            extra={"ojo": "datos parciales: Marketplace no publica m² estructurados"},
            **{k: v for k, v in datos.items() if k in
               ("precio", "moneda", "m2_totales", "ambientes", "dormitorios")},
        )


def _desescapar(s: str) -> str:
    try:
        return json.loads(f'"{s}"')
    except ValueError:
        return s.replace("\\u00e1", "á").replace("\\/", "/")
