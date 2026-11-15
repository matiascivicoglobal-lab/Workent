"""WhatsApp vía CallMeBot — gratis y sin servidor.

Alta (una sola vez, 2 minutos):
  1. Mirá el número vigente en https://www.callmebot.com/blog/free-api-whatsapp-messages/
     (cambia cada tanto; el histórico es +34 644 51 95 23).
  2. Agendalo y mandale por WhatsApp:  I allow callmebot to send me messages
  3. Te responde con tu apikey. Ponela en el .env como CALLMEBOT_APIKEY.

OJO: es un servicio gratuito de una sola persona y se llena seguido. Si te
responde "This Bot is full", no hay nada que configurar de este lado: hay que
esperar a que habilite un bot nuevo. Mientras tanto usá otro canal
(telegram es el reemplazo más rápido). Ver el README.

Límite: ~1 mensaje cada 20 segundos. Para avisos personales alcanza y sobra.
"""

from __future__ import annotations

import time

import httpx

from .base import Notificador

URL = "https://api.callmebot.com/whatsapp.php"


class CallMeBot(Notificador):
    nombre = "callmebot"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.apikey = ajustes.secreto("CALLMEBOT_APIKEY")

    def configurado(self) -> tuple[bool, str]:
        if not self.apikey:
            return False, (
                "Falta CALLMEBOT_APIKEY en el .env. Se pide mandando "
                "'I allow callmebot to send me messages' al número que figura en "
                "callmebot.com/blog/free-api-whatsapp-messages/. "
                "Si te contesta 'This Bot is full', el servicio no está tomando "
                "usuarios nuevos: usá --canal telegram o configurá whatsapp:cloud.")
        if not self.telefono:
            return False, "Falta alertas.telefono en config.yaml"
        return True, ""

    def enviar(self, mensaje: str) -> bool:
        listo, falta = self.configurado()
        if not listo:
            self.log.error("%s", falta)
            return False
        params = {"phone": self.e164(self.telefono), "text": mensaje,
                  "apikey": self.apikey}
        try:
            r = httpx.get(URL, params=params, timeout=30)
        except httpx.HTTPError as e:
            self.log.error("No pude enviar por CallMeBot: %s", e)
            return False
        cuerpo = (r.text or "")[:300]
        if r.status_code == 200 and "error" not in cuerpo.lower():
            time.sleep(21)       # respeta el límite de 1 msg / 20 s
            return True
        self.log.error("CallMeBot respondió %d: %s", r.status_code, cuerpo)
        return False
