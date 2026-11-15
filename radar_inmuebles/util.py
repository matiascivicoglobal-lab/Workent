"""Utilidades de parseo para avisos inmobiliarios argentinos."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------

def normalizar(texto: str | None) -> str:
    """Minúsculas, sin acentos, sin espacios de más."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")


def hash_corto(*partes: object) -> str:
    crudo = "|".join(str(p) for p in partes)
    return hashlib.sha1(crudo.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Números y precios
# ---------------------------------------------------------------------------

# En Argentina el punto es separador de miles y la coma es decimal.
_NUMERO = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?|\d+(?:\.\d+)?")

_SIN_PRECIO = (
    "consultar", "a consultar", "consulte", "precio a convenir",
    "no disponible", "reservado",
)


def parse_numero(texto: str | None) -> float | None:
    """'1.234,5' -> 1234.5 ; '68 m2' -> 68 ; '68.5' -> 68.5"""
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return float(texto)
    m = _NUMERO.search(str(texto).replace("\xa0", " "))
    if not m:
        return None
    crudo = m.group(0)
    if "." in crudo and "," in crudo:            # 1.234,56
        crudo = crudo.replace(".", "").replace(",", ".")
    elif "," in crudo:                            # 1234,56
        crudo = crudo.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", crudo):   # 1.234.567 -> miles
        crudo = crudo.replace(".", "")
    try:
        return float(crudo)
    except ValueError:
        return None


def detectar_moneda(texto: str) -> str | None:
    t = normalizar(texto)
    if re.search(r"\b(u\$s|us\$|usd|u\$d|dolares|dolar)\b", t) or "u$s" in t or "us$" in t:
        return "USD"
    if re.search(r"\b(ar\$|\$ar|pesos|ars)\b", t) or "$" in t:
        return "ARS"
    return None


def parse_precio(texto: str | None) -> tuple[float | None, str | None]:
    """'U$S 95.000' -> (95000.0, 'USD') ; '$ 120.000.000' -> (1.2e8, 'ARS')"""
    if not texto:
        return None, None
    t = str(texto)
    if any(p in normalizar(t) for p in _SIN_PRECIO):
        return None, None
    return parse_numero(t), detectar_moneda(t)


def parse_m2(texto: str | None) -> float | None:
    """Extrae metros cuadrados. Descarta valores absurdos."""
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        v = float(texto)
    else:
        t = normalizar(texto)
        m = re.search(r"([\d.,]+)\s*(?:m2|m²|mts2|mts|metros)", t)
        v = parse_numero(m.group(1)) if m else parse_numero(t)
    if v is None or not (10 <= v <= 1500):
        return None
    return v


def parse_ambientes(texto: str | None) -> int | None:
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        v = int(texto)
        return v if 1 <= v <= 12 else None
    t = normalizar(texto)
    if "monoambiente" in t:
        return 1
    m = re.search(r"(\d+)\s*(?:amb|ambiente)", t)
    if not m:
        m = re.search(r"^(\d+)$", t.strip())
    if not m:
        return None
    v = int(m.group(1))
    return v if 1 <= v <= 12 else None


def parse_entero(texto: str | None) -> int | None:
    v = parse_numero(texto)
    return int(v) if v is not None else None


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------

def ahora() -> datetime:
    return datetime.now(timezone.utc)


def parse_fecha(valor) -> datetime | None:
    """Acepta ISO8601, epoch (seg/ms) o 'hace N días'."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    if isinstance(valor, (int, float)):
        seg = float(valor) / 1000 if float(valor) > 1e11 else float(valor)
        try:
            return datetime.fromtimestamp(seg, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    t = str(valor).strip()
    m = re.search(r"hace\s+(\d+)\s*(dia|día|hora|mes|semana|ano|año)", normalizar(t))
    if m:
        n = int(m.group(1))
        unidad = m.group(2)
        dias = {"hora": n / 24, "dia": n, "día": n, "semana": n * 7,
                "mes": n * 30, "ano": n * 365, "año": n * 365}[unidad]
        return ahora() - timedelta(days=dias)
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(t[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def dias_desde(fecha: datetime | None) -> int | None:
    if fecha is None:
        return None
    if not fecha.tzinfo:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return max(0, (ahora() - fecha).days)


# ---------------------------------------------------------------------------
# Estadística robusta
# ---------------------------------------------------------------------------

def percentil(valores: list[float], p: float) -> float | None:
    """Percentil por interpolación lineal. p en 0..1."""
    xs = sorted(v for v in valores if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    pos = p * (len(xs) - 1)
    bajo = int(pos)
    alto = min(bajo + 1, len(xs) - 1)
    frac = pos - bajo
    return xs[bajo] * (1 - frac) + xs[alto] * frac


def mediana(valores: list[float]) -> float | None:
    return percentil(valores, 0.5)


def sin_outliers(valores: list[float], factor: float = 1.5) -> list[float]:
    """Recorte por rango intercuartílico (Tukey)."""
    xs = [v for v in valores if v is not None]
    if len(xs) < 5:
        return xs
    q1, q3 = percentil(xs, 0.25), percentil(xs, 0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return xs
    lo, hi = q1 - factor * iqr, q3 + factor * iqr
    return [v for v in xs if lo <= v <= hi]
