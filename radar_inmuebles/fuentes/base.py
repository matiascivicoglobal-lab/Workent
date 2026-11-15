"""Contrato común de las fuentes de avisos."""

from __future__ import annotations

import logging

log = logging.getLogger("radar.fuentes")


class Fuente:
    nombre: str = "base"
    requiere_navegador: bool = False

    def __init__(self, cliente, ajustes, navegador=None):
        self.cliente = cliente
        self.cfg = ajustes
        self.navegador = navegador
        self.log = logging.getLogger(f"radar.{self.nombre}")

    # -- a implementar por cada fuente ------------------------------------
    def buscar(self, barrio: str) -> list:
        """Lista de Aviso para un barrio. Nunca debe lanzar: devolver []."""
        raise NotImplementedError

    def enriquecer(self, aviso):
        """Opcional: abre la ficha y completa descripción/fecha/m². In-place."""
        return aviso

    # -- helpers -----------------------------------------------------------
    @property
    def paginas(self) -> int:
        return int(self.cfg.get("scraping.paginas_por_barrio", 3))

    def seguro(self, barrio: str) -> list:
        """Envoltorio que aísla fallas: una fuente rota no corta la corrida."""
        try:
            avisos = self.buscar(barrio) or []
            self.log.info("  %s/%s: %d avisos", self.nombre, barrio, len(avisos))
            return avisos
        except Exception as e:                      # noqa: BLE001 - aislamiento a propósito
            self.log.warning("  %s/%s falló: %s: %s", self.nombre, barrio,
                             type(e).__name__, e)
            self.log.debug("  detalle", exc_info=True)
            return []
