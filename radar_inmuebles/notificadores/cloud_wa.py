"""WhatsApp Cloud API (Meta) — la vía oficial y gratuita.

Es la única forma de mandarte WhatsApp a vos mismo, para siempre, sin depender
de un servicio de terceros. A cambio, Meta impone dos reglas:

  1. Sin plantilla aprobada solo podés escribir dentro de las 24 h posteriores
     a un mensaje TUYO al bot. Para avisos automáticos eso no sirve: necesitás
     una plantilla (categoría "Utility", se aprueba en minutos u horas).
  2. Las variables de plantilla NO admiten saltos de línea. Por eso el aviso
     se aplana a una sola línea con separadores. Se lee peor que por Telegram
     o CallMeBot, pero llega siempre.

.env:
  WA_PHONE_NUMBER_ID=123456789
  WA_TOKEN=EAAG...                 (token permanente de system user)
  WA_TEMPLATE=aviso_propiedad      (nombre de la plantilla aprobada)
  WA_TEMPLATE_LANG=es              (el idioma con el que la aprobaste)
"""

from __future__ import annotations

import re

import httpx

from .base import Notificador

VERSION = "v21.0"
# WhatsApp rechaza las variables de plantilla que traen saltos de línea,
# tabs o 4+ espacios seguidos. Hay que aplanar el mensaje antes de mandarlo.
LIMITE_VARIABLE = 900


def aplanar(mensaje: str) -> str:
    """Deja el aviso en una sola línea, apto para variable de plantilla."""
    texto = mensaje.replace("\t", " ")
    texto = re.sub(r"^[─·\s]+$", "", texto, flags=re.M)     # separadores sueltos
    texto = re.sub(r"\n+", " · ", texto)
    texto = re.sub(r"[ ]{2,}", " ", texto)
    texto = re.sub(r"(?: · )+", " · ", texto).strip(" ·")
    return texto[:LIMITE_VARIABLE]


class CloudWhatsApp(Notificador):
    nombre = "cloud"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.phone_id = ajustes.secreto("WA_PHONE_NUMBER_ID")
        self.token = ajustes.secreto("WA_TOKEN")
        self.plantilla = ajustes.secreto("WA_TEMPLATE")
        # Tiene que coincidir con el idioma con el que aprobaste la plantilla.
        self.idioma = ajustes.secreto("WA_TEMPLATE_LANG", "es")

    def configurado(self) -> tuple[bool, str]:
        if not (self.phone_id and self.token):
            return False, "Faltan WA_PHONE_NUMBER_ID / WA_TOKEN en el .env"
        return True, ""

    def enviar(self, mensaje: str) -> bool:
        listo, falta = self.configurado()
        if not listo:
            self.log.error("%s", falta)
            return False
        destino = self.e164(self.telefono).lstrip("+")
        url = f"https://graph.facebook.com/{VERSION}/{self.phone_id}/messages"
        if self.plantilla:
            cuerpo = {
                "messaging_product": "whatsapp", "to": destino, "type": "template",
                "template": {"name": self.plantilla, "language": {"code": self.idioma},
                             "components": [{"type": "body", "parameters": [
                                 {"type": "text", "text": aplanar(mensaje)}]}]},
            }
        else:
            cuerpo = {"messaging_product": "whatsapp", "to": destino, "type": "text",
                      "text": {"preview_url": True, "body": mensaje}}
        try:
            r = httpx.post(url, json=cuerpo,
                           headers={"Authorization": f"Bearer {self.token}"}, timeout=30)
        except httpx.HTTPError as e:
            self.log.error("No pude enviar por Cloud API: %s", e)
            return False
        if r.status_code == 200:
            return True
        self.log.error("Cloud API respondió %d: %s", r.status_code, r.text[:300])
        return False
