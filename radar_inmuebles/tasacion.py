"""Valor de referencia por zona: cuánto vale el m² en cada barrio.

Estrategia: el propio radar arma la mediana de USD/m² con todo lo que
publicaron los portales (muestra propia). Hasta tener muestra suficiente usa
los valores semilla del config.yaml. Siempre recorta outliers por IQR, porque
el corpus incluye justamente las gangas y los delirios que queremos detectar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .util import mediana, normalizar, percentil, sin_outliers

log = logging.getLogger("radar.tasacion")

# Rango plausible de USD/m² para CABA. Fuera de esto es error de carga,
# cochera vendida como depto, o un precio en pesos mal etiquetado.
PM2_MIN = 450
PM2_MAX = 7000


@dataclass
class Referencia:
    barrio: str
    mediana: float
    p25: float
    p75: float
    n: int
    origen: str            # "propia" | "mixta" | "semilla"

    @property
    def confianza(self) -> str:
        if self.origen == "propia" and self.n >= 40:
            return "alta"
        if self.origen in ("propia", "mixta") and self.n >= 15:
            return "media"
        return "baja"

    def __str__(self) -> str:
        return (f"{self.barrio}: USD {self.mediana:,.0f}/m² "
                f"(p25 {self.p25:,.0f} · p75 {self.p75:,.0f} · n={self.n} · {self.origen})")


class Tasador:
    def __init__(self, almacen, ajustes):
        self.almacen = almacen
        self.cfg = ajustes
        self.semillas = ajustes.valores_referencia
        self.min_muestra = int(ajustes.get("oportunidad.muestra_minima", 20))
        self.segmentar = bool(ajustes.get("oportunidad.segmentar_por_ambientes", False))
        self._cache: dict[str, Referencia] = {}

    # ------------------------------------------------------------------
    def referencia(self, barrio: str, ambientes: int | None = None) -> Referencia | None:
        clave = f"{normalizar(barrio)}|{ambientes if self.segmentar else ''}"
        if clave in self._cache:
            return self._cache[clave]
        ref = self._calcular(barrio, ambientes)
        if ref:
            self._cache[clave] = ref
        return ref

    def invalidar(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------
    def _muestra(self, barrio: str, ambientes: int | None) -> list[float]:
        valores: list[float] = []
        for a in self.almacen.avisos(barrio=barrio, dias=180):
            if self.segmentar and ambientes and a.ambientes != ambientes:
                continue
            if a.tipo not in ("departamento", "ph"):
                continue
            pm2 = a.precio_m2()
            if pm2 and PM2_MIN <= pm2 <= PM2_MAX:
                valores.append(pm2)
        return sin_outliers(valores)

    def _semilla(self, barrio: str) -> float | None:
        b = normalizar(barrio)
        if b in self.semillas:
            return self.semillas[b]
        for k, v in self.semillas.items():          # "caballito norte" -> "caballito"
            if normalizar(k) in b or b in normalizar(k):
                return v
        return None

    def _calcular(self, barrio: str, ambientes: int | None) -> Referencia | None:
        muestra = self._muestra(barrio, ambientes)
        semilla = self._semilla(barrio)
        n = len(muestra)

        if n >= self.min_muestra:
            return Referencia(barrio, mediana(muestra), percentil(muestra, 0.25),
                              percentil(muestra, 0.75), n, "propia")

        if n >= max(5, self.min_muestra // 2) and semilla:
            # Mezcla ponderada: cuanta más muestra propia, menos pesa la semilla.
            peso = n / self.min_muestra
            med = mediana(muestra) * peso + semilla * (1 - peso)
            return Referencia(barrio, med, med * 0.85, med * 1.18, n, "mixta")

        if semilla:
            return Referencia(barrio, semilla, semilla * 0.85, semilla * 1.18, n, "semilla")

        if n >= 5:
            return Referencia(barrio, mediana(muestra), percentil(muestra, 0.25),
                              percentil(muestra, 0.75), n, "propia")

        log.debug("Sin referencia para %s (n=%d, sin semilla)", barrio, n)
        return None

    # ------------------------------------------------------------------
    def todas(self, barrios: list[str]) -> list[Referencia]:
        refs = [self.referencia(b) for b in barrios]
        return [r for r in refs if r]
