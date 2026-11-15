"""Cotización del dólar para normalizar avisos publicados en pesos."""

from __future__ import annotations

import logging

log = logging.getLogger("radar.cotizacion")

FUENTES = {
    "blue":    "https://dolarapi.com/v1/dolares/blue",
    "mep":     "https://dolarapi.com/v1/dolares/bolsa",
    "oficial": "https://dolarapi.com/v1/dolares/oficial",
}
RESPALDO = "https://api.bluelytics.com.ar/v2/latest"


def obtener(cliente, almacen, tipo: str = "blue", manual: float = 1450.0) -> float:
    """Devuelve ARS por USD. Cachea una vez por día en la base."""
    if tipo == "manual":
        return float(manual)

    cacheada = almacen.cotizacion_de_hoy()
    if cacheada:
        return cacheada

    url = FUENTES.get(tipo, FUENTES["blue"])
    datos = cliente.json(url)
    valor = None
    if isinstance(datos, dict):
        valor = datos.get("venta") or datos.get("compra")

    if not valor:
        datos = cliente.json(RESPALDO)
        if isinstance(datos, dict):
            clave = "blue" if tipo != "oficial" else "oficial"
            valor = (datos.get(clave) or {}).get("value_sell")

    if not valor:
        anterior = almacen.ultima_cotizacion()
        if anterior:
            log.warning("No pude actualizar el dólar, uso la última guardada: %.0f", anterior)
            return anterior
        log.warning("No pude obtener el dólar, uso el valor manual: %.0f", manual)
        return float(manual)

    valor = float(valor)
    almacen.guardar_cotizacion(tipo, valor)
    log.info("Dólar %s: $%.0f", tipo, valor)
    return valor


def a_usd(precio: float | None, moneda: str | None, usd_ars: float) -> float | None:
    if precio is None or precio <= 0:
        return None
    if moneda == "USD" or moneda is None:
        # Sin moneda explícita asumimos USD: en CABA la venta se publica en dólares.
        return float(precio)
    if moneda == "ARS":
        if usd_ars <= 0:
            return None
        return float(precio) / usd_ars
    return float(precio)
