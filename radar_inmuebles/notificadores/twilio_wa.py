"""WhatsApp vía Twilio — pago, pero es el más confiable para volumen.

.env:
  TWILIO_ACCOUNT_SID=ACxxxxxxxx
  TWILIO_AUTH_TOKEN=xxxxxxxx
  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886     (sandbox) o tu número aprobado
"""

from __future__ import annotations

import httpx

from .base import Notificador


class TwilioWhatsApp(Notificador):
    nombre = "twilio"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.sid = ajustes.secreto("TWILIO_ACCOUNT_SID")
        self.token = ajustes.secreto("TWILIO_AUTH_TOKEN")
        self.origen = ajustes.secreto("TWILIO_WHATSAPP_FROM",
                                      "whatsapp:+14155238886")

    def configurado(self) -> tuple[bool, str]:
        if not (self.sid and self.token):
            return False, "Faltan TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN en el .env"
        return True, ""

    def enviar(self, mensaje: str) -> bool:
        listo, falta = self.configurado()
        if not listo:
            self.log.error("%s", falta)
            return False
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json"
        origen = self.origen if self.origen.startswith("whatsapp:") else f"whatsapp:{self.origen}"
        datos = {"From": origen, "To": f"whatsapp:{self.e164(self.telefono)}",
                 "Body": mensaje}
        try:
            r = httpx.post(url, data=datos, auth=(self.sid, self.token), timeout=30)
        except httpx.HTTPError as e:
            self.log.error("No pude enviar por Twilio: %s", e)
            return False
        if r.status_code in (200, 201):
            return True
        self.log.error("Twilio respondió %d: %s", r.status_code, r.text[:300])
        return False
