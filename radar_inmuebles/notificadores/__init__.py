"""Selección del canal de aviso según config.yaml."""

from __future__ import annotations

import logging

from .base import Notificador
from .callmebot import CallMeBot
from .cloud_wa import CloudWhatsApp
from .consola import Consola
from .telegram import Telegram
from .twilio_wa import TwilioWhatsApp

log = logging.getLogger("radar.notificador")

WHATSAPP = {"callmebot": CallMeBot, "twilio": TwilioWhatsApp, "cloud": CloudWhatsApp}


def construir_notificador(ajustes) -> Notificador:
    destino = str(ajustes.get("alertas.destino", "consola")).lower()
    if destino == "whatsapp":
        proveedor = str(ajustes.get("alertas.proveedor_whatsapp", "callmebot")).lower()
        clase = WHATSAPP.get(proveedor)
        if not clase:
            log.warning("Proveedor de WhatsApp desconocido '%s', uso consola", proveedor)
            return Consola(ajustes)
        return clase(ajustes)
    if destino == "telegram":
        return Telegram(ajustes)
    return Consola(ajustes)


__all__ = ["Notificador", "construir_notificador", "Consola", "CallMeBot",
           "TwilioWhatsApp", "CloudWhatsApp", "Telegram"]
