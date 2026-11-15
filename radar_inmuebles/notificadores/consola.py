"""Salida por consola: para probar sin mandar nada."""

from __future__ import annotations

from .base import Notificador


class Consola(Notificador):
    nombre = "consola"

    def enviar(self, mensaje: str) -> bool:
        print("\n" + "=" * 46)
        print(mensaje)
        print("=" * 46 + "\n")
        return True
