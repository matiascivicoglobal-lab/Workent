"""WhatsApp Cloud API (Meta) — gratis para mensajes de servicio.

Ojo: para iniciar conversación fuera de la ventana de 24 h hace falta una
plantilla aprobada. Para avisarte a vos mismo conviene CallMeBot o Telegram.

.env:
  WA_PHONE_NUMBER_ID=123456789
  WA_TOKEN=EAAG...
  WA_TEMPLATE=         (opcional: nombre de plantilla aprobada)
"""

from __future__ import annotations

import httpx

from .base import Notificador

VERSION = "v21.0"


class CloudWhatsApp(Notificador):
    nombre = "cloud"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.phone_id = ajustes.secreto("WA_PHONE_NUMBER_ID")
        self.token = ajustes.secreto("WA_TOKEN")
        self.plantilla = ajustes.secreto("WA_TEMPLATE")

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
                "template": {"name": self.plantilla, "language": {"code": "es_AR"},
                             "components": [{"type": "body", "parameters": [
                                 {"type": "text", "text": mensaje[:1000]}]}]},
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
