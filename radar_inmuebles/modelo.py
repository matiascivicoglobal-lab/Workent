"""Modelo normalizado de aviso, común a todas las fuentes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .util import (dias_desde, hash_corto, normalizar, parse_ambientes,
                   parse_fecha, parse_m2, parse_numero)


@dataclass
class Aviso:
    fuente: str                      # "zonaprop", "mercadolibre", ...
    id_externo: str
    url: str
    titulo: str = ""
    barrio: str = ""
    direccion: str | None = None
    precio: float | None = None       # en la moneda publicada
    moneda: str | None = None         # "USD" | "ARS"
    precio_usd: float | None = None   # normalizado (lo completa el pipeline)
    expensas_ars: float | None = None
    m2_totales: float | None = None
    m2_cubiertos: float | None = None
    ambientes: int | None = None
    dormitorios: int | None = None
    banios: int | None = None
    antiguedad: int | None = None     # años de construcción
    piso: str | None = None
    publicado: datetime | None = None
    imagen: str | None = None
    descripcion: str = ""
    tipo: str = "departamento"        # departamento | ph | casa | otro
    extra: dict = field(default_factory=dict)

    # -- identidad ---------------------------------------------------------
    @property
    def id(self) -> str:
        return f"{self.fuente}:{self.id_externo}"

    def clave_dedupe(self) -> str:
        """Agrupa el mismo inmueble publicado en varios portales.

        Usa barrio + superficie redondeada a 5 m² + precio en escalones de
        USD 2.500 + ambientes. Dos avisos del mismo depto casi nunca difieren
        más que eso; dos deptos distintos rara vez coinciden en los cuatro.
        """
        m2 = self.m2_ref()
        if not m2 or not self.precio_usd:
            return self.id
        return hash_corto(
            normalizar(self.barrio),
            round(m2 / 5) * 5,
            round(self.precio_usd / 2500) * 2500,
            self.ambientes or 0,
        )

    # -- derivados ---------------------------------------------------------
    def m2_ref(self) -> float | None:
        """Superficie de referencia: cubierta si existe, si no total."""
        return self.m2_cubiertos or self.m2_totales

    def precio_m2(self) -> float | None:
        m2 = self.m2_ref()
        if not m2 or not self.precio_usd:
            return None
        return self.precio_usd / m2

    def dias_publicado(self) -> int | None:
        return dias_desde(self.publicado)

    def texto_completo(self) -> str:
        return normalizar(f"{self.titulo} {self.descripcion} {self.direccion or ''}")

    def completo(self) -> bool:
        """¿Alcanza para tasarlo?"""
        return bool(self.precio_usd and self.m2_ref() and self.url)

    # -- serialización -----------------------------------------------------
    def a_dict(self) -> dict:
        d = asdict(self)
        d["publicado"] = self.publicado.isoformat() if self.publicado else None
        d["id"] = self.id
        return d

    @classmethod
    def desde_dict(cls, d: dict) -> "Aviso":
        datos = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        datos["publicado"] = parse_fecha(datos.get("publicado"))
        if isinstance(datos.get("extra"), str):
            try:
                datos["extra"] = json.loads(datos["extra"])
            except (ValueError, TypeError):
                datos["extra"] = {}
        return cls(**datos)

    def __str__(self) -> str:
        p = f"USD {self.precio_usd:,.0f}" if self.precio_usd else "s/precio"
        m = f"{self.m2_ref():.0f}m²" if self.m2_ref() else "s/m²"
        return f"[{self.fuente}] {self.barrio} · {self.ambientes or '?'}amb · {m} · {p}"


def construir(fuente: str, id_externo: str, url: str, **campos) -> Aviso:
    """Constructor tolerante: parsea strings crudos de los portales."""
    campos["ambientes"] = parse_ambientes(campos.get("ambientes"))
    campos["dormitorios"] = parse_ambientes(campos.get("dormitorios"))
    campos["m2_totales"] = parse_m2(campos.get("m2_totales"))
    campos["m2_cubiertos"] = parse_m2(campos.get("m2_cubiertos"))
    campos["publicado"] = parse_fecha(campos.get("publicado"))
    for k in ("precio", "expensas_ars", "antiguedad", "banios"):
        if k in campos and not isinstance(campos[k], (int, float, type(None))):
            campos[k] = parse_numero(campos[k])
    campos = {k: v for k, v in campos.items() if k in Aviso.__dataclass_fields__}
    return Aviso(fuente=fuente, id_externo=str(id_externo), url=url, **campos)
