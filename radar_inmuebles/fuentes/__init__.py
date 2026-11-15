"""Registro de fuentes. Agregar una fuente nueva = agregarla a este dict."""

from __future__ import annotations

import logging

from .argenprop import Argenprop
from .base import Fuente
from .facebook import Facebook
from .mercadolibre import MercadoLibre
from .properati import Properati
from .remax import Remax
from .zonaprop import Zonaprop

log = logging.getLogger("radar.fuentes")

REGISTRO: dict[str, type[Fuente]] = {
    MercadoLibre.nombre: MercadoLibre,
    Argenprop.nombre: Argenprop,
    Properati.nombre: Properati,
    Remax.nombre: Remax,
    Zonaprop.nombre: Zonaprop,
    Facebook.nombre: Facebook,
}


def construir_fuentes(nombres, cliente, ajustes, navegador=None) -> list[Fuente]:
    fuentes = []
    for nombre in nombres:
        clase = REGISTRO.get(nombre)
        if not clase:
            log.warning("Fuente desconocida en config.yaml: %s", nombre)
            continue
        if clase.requiere_navegador and navegador is None:
            log.warning("Salteo '%s': necesita Playwright y no está disponible", nombre)
            continue
        fuentes.append(clase(cliente, ajustes, navegador))
    return fuentes


__all__ = ["REGISTRO", "construir_fuentes", "Fuente"]
