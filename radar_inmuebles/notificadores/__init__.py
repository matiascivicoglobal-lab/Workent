"""Selección del canal de aviso según config.yaml."""

from __future__ import annotations

import logging

from .base import Notificador
from .cadena import Cadena
from .callmebot import CallMeBot
from .cloud_wa import CloudWhatsApp
from .consola import Consola
from .telegram import Telegram
from .twilio_wa import TwilioWhatsApp

log = logging.getLogger("radar.notificador")

WHATSAPP = {"callmebot": CallMeBot, "twilio": TwilioWhatsApp, "cloud": CloudWhatsApp}


def construir_canal(ajustes, destino: str, proveedor: str = "") -> Notificador:
    """Un canal suelto. `destino` es whatsapp | telegram | consola."""
    destino = (destino or "consola").lower().strip()
    if destino == "whatsapp":
        proveedor = (proveedor or ajustes.get("alertas.proveedor_whatsapp",
                                              "callmebot")).lower().strip()
        clase = WHATSAPP.get(proveedor)
        if not clase:
            log.warning("Proveedor de WhatsApp desconocido '%s'. Opciones: %s",
                        proveedor, ", ".join(WHATSAPP))
            return Consola(ajustes)
        return clase(ajustes)
    if destino == "telegram":
        return Telegram(ajustes)
    if destino == "consola":
        return Consola(ajustes)
    log.warning("Destino desconocido '%s', uso consola", destino)
    return Consola(ajustes)


def parsear_canal(texto: str) -> tuple[str, str]:
    """'whatsapp:twilio' -> ('whatsapp', 'twilio')"""
    destino, _, proveedor = (texto or "").partition(":")
    return destino.strip(), proveedor.strip()


def construir_notificador(ajustes, canal: str = "") -> Notificador:
    """Canal principal, con el de respaldo detrás si está configurado.

    `canal` (ej. 'telegram' o 'whatsapp:twilio') pisa la config: sirve para
    probar sin editar el archivo.
    """
    if canal:
        destino, proveedor = parsear_canal(canal)
        return construir_canal(ajustes, destino, proveedor)

    principal = construir_canal(ajustes, str(ajustes.get("alertas.destino", "consola")))

    respaldo_cfg = str(ajustes.get("alertas.respaldo", "") or "").strip()
    if not respaldo_cfg:
        return principal

    destino, proveedor = parsear_canal(respaldo_cfg)
    respaldo = construir_canal(ajustes, destino, proveedor)
    if respaldo.nombre == principal.nombre:
        return principal
    return Cadena(ajustes, [principal, respaldo])


__all__ = ["Notificador", "construir_notificador", "construir_canal", "parsear_canal",
           "Cadena", "Consola", "CallMeBot", "TwilioWhatsApp", "CloudWhatsApp",
           "Telegram"]
