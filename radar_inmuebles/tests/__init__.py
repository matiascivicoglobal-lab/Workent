"""Tests del radar. Todos corren sin red."""

from pathlib import Path

from radar_inmuebles.ajustes import cargar

CONFIG_TEST = Path(__file__).parent / "config_test.yaml"


def cfg_test():
    """Configuración fija de los tests, independiente del config.yaml del usuario."""
    return cargar(CONFIG_TEST, recargar=True)
