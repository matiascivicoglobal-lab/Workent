"""Carga de configuración: config.yaml + variables de entorno (.env)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parent
CONFIG_DEFECTO = RAIZ / "config.yaml"


def _cargar_env() -> None:
    """Carga .env del paquete o del repo, sin pisar variables ya definidas."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for ruta in (RAIZ / ".env", RAIZ.parent / ".env"):
        if ruta.exists():
            load_dotenv(ruta, override=False)


class Ajustes:
    def __init__(self, ruta: str | Path | None = None):
        _cargar_env()
        self.ruta = Path(ruta or os.getenv("RADAR_CONFIG") or CONFIG_DEFECTO)
        if not self.ruta.exists():
            raise FileNotFoundError(f"No encuentro la configuración: {self.ruta}")
        with open(self.ruta, encoding="utf-8") as f:
            self.datos: dict[str, Any] = yaml.safe_load(f) or {}

    # -- acceso por ruta con puntos: cfg.get("alertas.telefono") -----------
    def get(self, camino: str, defecto: Any = None) -> Any:
        nodo: Any = self.datos
        for parte in camino.split("."):
            if not isinstance(nodo, dict) or parte not in nodo:
                return defecto
            nodo = nodo[parte]
        return nodo

    def __getitem__(self, camino: str) -> Any:
        return self.get(camino)

    # -- secciones de uso frecuente ---------------------------------------
    @property
    def busqueda(self) -> dict:
        return self.datos.get("busqueda", {})

    @property
    def barrios(self) -> list[str]:
        return [str(b).strip().lower() for b in self.get("busqueda.barrios", [])]

    @property
    def fuentes_activas(self) -> list[str]:
        f = self.datos.get("fuentes", {})
        return [n for n, c in f.items() if isinstance(c, dict) and c.get("activa")]

    def fuente_usa_navegador(self, nombre: str) -> bool:
        return bool(self.get(f"fuentes.{nombre}.navegador", False))

    @property
    def valores_referencia(self) -> dict[str, float]:
        crudo = self.datos.get("valores_referencia", {}) or {}
        return {str(k).strip().lower(): float(v) for k, v in crudo.items()}

    # -- rutas -------------------------------------------------------------
    def ruta_datos(self, camino: str) -> Path:
        p = Path(camino)
        if not p.is_absolute():
            p = RAIZ / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db(self) -> Path:
        return self.ruta_datos(self.get("salida.db", "datos/radar.sqlite3"))

    @property
    def reporte_html(self) -> Path:
        return self.ruta_datos(self.get("salida.reporte_html", "datos/reporte.html"))

    # -- secretos (siempre desde el entorno, nunca del YAML) ---------------
    @staticmethod
    def secreto(nombre: str, defecto: str = "") -> str:
        return os.getenv(nombre, defecto).strip()


_cache: Ajustes | None = None


def cargar(ruta: str | Path | None = None, recargar: bool = False) -> Ajustes:
    global _cache
    if _cache is None or recargar or ruta:
        _cache = Ajustes(ruta)
    return _cache
