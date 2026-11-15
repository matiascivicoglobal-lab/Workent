"""Contrato de los notificadores."""

from __future__ import annotations

import logging

log = logging.getLogger("radar.notificador")


class Notificador:
    nombre = "base"

    def __init__(self, ajustes):
        self.cfg = ajustes
        self.telefono = str(ajustes.get("alertas.telefono", "")).strip()
        self.log = logging.getLogger(f"radar.{self.nombre}")

    def enviar(self, mensaje: str) -> bool:
        raise NotImplementedError

    def configurado(self) -> tuple[bool, str]:
        """(listo, qué falta)"""
        return True, ""

    @staticmethod
    def e164(telefono: str) -> str:
        """'1123549925' -> '+5491123549925' (celular de CABA)."""
        t = "".join(c for c in telefono if c.isdigit() or c == "+")
        if t.startswith("+"):
            return t
        t = t.lstrip("0")
        if t.startswith("54"):
            resto = t[2:]
            # Los celulares argentinos en E.164 llevan el 9: +549 11 ....
            if not resto.startswith("9") and len(resto) == 10:
                return "+549" + resto
            return "+" + t
        if len(t) == 10 and t.startswith("11"):     # 11 2354 9925
            return "+549" + t
        if len(t) == 8:                              # sin característica
            return "+54911" + t
        return "+" + t
