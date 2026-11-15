"""Canal con respaldo: si el principal falla, prueba el siguiente.

Sirve justamente para lo que pasa seguido con WhatsApp: el proveedor gratis
se cae, te quedás sin cupo o te expira un token. El aviso igual te llega.
"""

from __future__ import annotations

from .base import Notificador


class Cadena(Notificador):
    nombre = "cadena"

    def __init__(self, ajustes, canales: list[Notificador]):
        super().__init__(ajustes)
        self.canales = [c for c in canales if c]
        self.nombre = " → ".join(c.nombre for c in self.canales) or "vacío"

    def configurado(self) -> tuple[bool, str]:
        faltantes = []
        for canal in self.canales:
            listo, falta = canal.configurado()
            if listo:
                return True, ""
            faltantes.append(f"{canal.nombre}: {falta}")
        return False, " | ".join(faltantes) or "no hay ningún canal configurado"

    def enviar(self, mensaje: str) -> bool:
        for i, canal in enumerate(self.canales):
            listo, falta = canal.configurado()
            if not listo:
                self.log.debug("  salteo %s (%s)", canal.nombre, falta)
                continue
            if canal.enviar(mensaje):
                if i > 0:
                    self.log.warning("  el aviso salió por el respaldo (%s)", canal.nombre)
                return True
            self.log.warning("  %s falló, pruebo el siguiente canal", canal.nombre)
        self.log.error("  ningún canal pudo enviar el aviso")
        return False
