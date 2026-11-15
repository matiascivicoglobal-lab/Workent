"""Telegram — respaldo gratis, instantáneo y sin límites prácticos.

Alta: hablale a @BotFather, /newbot, copiá el token. Después escribile algo a
tu bot y mirá https://api.telegram.org/bot<TOKEN>/getUpdates para tu chat_id.

.env:
  TELEGRAM_TOKEN=123456:ABC...
  TELEGRAM_CHAT_ID=987654321
"""

from __future__ import annotations

import httpx

from .base import Notificador


class Telegram(Notificador):
    nombre = "telegram"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.token = ajustes.secreto("TELEGRAM_TOKEN")
        self.chat_id = ajustes.secreto("TELEGRAM_CHAT_ID")

    def configurado(self) -> tuple[bool, str]:
        if not (self.token and self.chat_id):
            return False, "Faltan TELEGRAM_TOKEN / TELEGRAM_CHAT_ID en el .env"
        return True, ""

    def enviar(self, mensaje: str) -> bool:
        listo, falta = self.configurado()
        if not listo:
            self.log.error("%s", falta)
            return False
        # Telegram usa *negrita* igual que WhatsApp en modo Markdown.
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            r = httpx.post(url, json={"chat_id": self.chat_id, "text": mensaje,
                                      "parse_mode": "Markdown",
                                      "disable_web_page_preview": False}, timeout=30)
        except httpx.HTTPError as e:
            self.log.error("No pude enviar por Telegram: %s", e)
            return False
        if r.status_code == 200:
            return True
        # Si el Markdown rompe, reintentamos en texto plano.
        if r.status_code == 400:
            r = httpx.post(url, json={"chat_id": self.chat_id, "text": mensaje},
                           timeout=30)
            if r.status_code == 200:
                return True
        self.log.error("Telegram respondió %d: %s", r.status_code, r.text[:300])
        return False
