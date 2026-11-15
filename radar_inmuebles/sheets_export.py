"""Exportar las oportunidades a Google Sheets (opcional).

Reusa el service account que ya está configurado en el repo
(credentials/service_account.json). Activalo con:
    salida.exportar_sheets: true
    salida.spreadsheet_id: "<id de la planilla>"
y compartí la planilla con el mail del service account.
"""

from __future__ import annotations

import logging
from datetime import datetime

log = logging.getLogger("radar.sheets")

ENCABEZADOS = ["Fecha", "Puntaje", "Barrio", "Amb", "m²", "Precio USD", "USD/m²",
               "Zona USD/m²", "Descuento", "Margen est.", "Días pub.", "Señales",
               "Fuente", "URL"]


def _fila(ev) -> list:
    a = ev.aviso
    m2 = a.m2_ref()
    return [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        round(ev.puntaje, 1),
        a.barrio.title(),
        a.ambientes or "",
        round(m2) if m2 else "",
        round(a.precio_usd) if a.precio_usd else "",
        round(ev.precio_m2) if ev.precio_m2 else "",
        round(ev.referencia.mediana) if ev.referencia else "",
        f"{ev.descuento * 100:.0f}%" if ev.descuento is not None else "",
        round(ev.margen) if ev.margen else "",
        ev.dias_publicado if ev.dias_publicado is not None else "",
        ", ".join(ev.senales[:4]),
        a.fuente,
        a.url,
    ]


def exportar(evaluaciones, ajustes) -> bool:
    if not ajustes.get("salida.exportar_sheets"):
        return False
    sid = str(ajustes.get("salida.spreadsheet_id", "")).strip()
    if not sid:
        log.warning("exportar_sheets está activo pero falta salida.spreadsheet_id")
        return False
    if not evaluaciones:
        return False

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        log.warning("Para exportar a Sheets: pip install gspread google-auth")
        return False

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from config import get_service_account_credentials      # type: ignore

        creds = Credentials.from_service_account_info(
            get_service_account_credentials(),
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
        hoja = gspread.authorize(creds).open_by_key(sid)
        try:
            ws = hoja.worksheet("Oportunidades")
        except Exception:                               # noqa: BLE001
            ws = hoja.add_worksheet("Oportunidades", rows=1000, cols=len(ENCABEZADOS))
            ws.append_row(ENCABEZADOS)

        filas = [_fila(ev) for ev in
                 sorted(evaluaciones, key=lambda e: e.puntaje, reverse=True)]
        ws.append_rows(filas, value_input_option="USER_ENTERED")
        log.info("Exportadas %d filas a Google Sheets", len(filas))
        return True
    except Exception as e:                              # noqa: BLE001
        log.warning("No pude exportar a Sheets: %s: %s", type(e).__name__, e)
        return False
