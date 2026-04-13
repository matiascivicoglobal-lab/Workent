"""
Google Sheets client.
Soporta: leer, escribir, crear hojas, y exportar reportes de Google Ads.
Autenticación via Service Account.
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import Any

from config import get_service_account_credentials, DEFAULT_SPREADSHEET_ID, DEFAULT_SHEET_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    def __init__(self):
        creds_dict = get_service_account_credentials()
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        self._client = gspread.authorize(creds)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def open(self, spreadsheet_id: str = "") -> gspread.Spreadsheet:
        sid = spreadsheet_id or DEFAULT_SPREADSHEET_ID
        if not sid:
            raise ValueError("Especificá un spreadsheet_id o configurá DEFAULT_SPREADSHEET_ID en .env")
        return self._client.open_by_key(sid)

    def get_sheet(self, sheet_name: str = "", spreadsheet_id: str = "") -> gspread.Worksheet:
        name = sheet_name or DEFAULT_SHEET_NAME
        return self.open(spreadsheet_id).worksheet(name)

    # ------------------------------------------------------------------
    # Leer
    # ------------------------------------------------------------------

    def read_all(self, sheet_name: str = "", spreadsheet_id: str = "") -> list[dict]:
        """Devuelve todas las filas como lista de dicts (primera fila = headers)."""
        ws = self.get_sheet(sheet_name, spreadsheet_id)
        return ws.get_all_records()

    def read_range(self, range_: str, sheet_name: str = "", spreadsheet_id: str = "") -> list[list]:
        """Lee un rango A1 notation, e.g. 'A1:D10'."""
        ws = self.get_sheet(sheet_name, spreadsheet_id)
        return ws.get(range_)

    # ------------------------------------------------------------------
    # Escribir
    # ------------------------------------------------------------------

    def append_rows(self, rows: list[list], sheet_name: str = "", spreadsheet_id: str = "") -> dict:
        """Agrega filas al final de la hoja."""
        ws = self.get_sheet(sheet_name, spreadsheet_id)
        return ws.append_rows(rows, value_input_option="USER_ENTERED")

    def update_range(
        self, range_: str, values: list[list], sheet_name: str = "", spreadsheet_id: str = ""
    ) -> dict:
        """Actualiza un rango específico, e.g. range_='A2:C5'."""
        ws = self.get_sheet(sheet_name, spreadsheet_id)
        return ws.update(range_, values, value_input_option="USER_ENTERED")

    def clear_sheet(self, sheet_name: str = "", spreadsheet_id: str = "") -> dict:
        """Borra todo el contenido de la hoja (mantiene la hoja)."""
        ws = self.get_sheet(sheet_name, spreadsheet_id)
        return ws.clear()

    # ------------------------------------------------------------------
    # Crear hojas
    # ------------------------------------------------------------------

    def create_spreadsheet(self, title: str) -> gspread.Spreadsheet:
        """Crea una nueva spreadsheet y la devuelve."""
        return self._client.create(title)

    def add_sheet(self, sheet_name: str, spreadsheet_id: str = "", rows: int = 1000, cols: int = 26) -> gspread.Worksheet:
        """Agrega una nueva pestaña a una spreadsheet existente."""
        ss = self.open(spreadsheet_id)
        return ss.add_worksheet(title=sheet_name, rows=rows, cols=cols)

    def get_or_create_sheet(self, sheet_name: str, spreadsheet_id: str = "") -> gspread.Worksheet:
        """Devuelve la hoja si existe, sino la crea."""
        ss = self.open(spreadsheet_id)
        try:
            return ss.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return ss.add_worksheet(title=sheet_name, rows=1000, cols=26)

    # ------------------------------------------------------------------
    # Exportar reportes (Google Ads -> Sheets)
    # ------------------------------------------------------------------

    def export_report(
        self,
        report_data: list[dict[str, Any]],
        sheet_name: str,
        spreadsheet_id: str = "",
        overwrite: bool = True,
    ) -> None:
        """
        Escribe un reporte de Google Ads en una hoja.

        Args:
            report_data: Lista de dicts con los datos del reporte.
                         Las keys del primer dict se usan como headers.
            sheet_name:  Nombre de la pestaña destino (se crea si no existe).
            spreadsheet_id: ID de la spreadsheet (usa DEFAULT si no se pasa).
            overwrite:   Si True, borra la hoja antes de escribir.
        """
        if not report_data:
            return

        ws = self.get_or_create_sheet(sheet_name, spreadsheet_id)

        if overwrite:
            ws.clear()

        headers = list(report_data[0].keys())
        rows = [headers] + [[row.get(h, "") for h in headers] for row in report_data]
        ws.update("A1", rows, value_input_option="USER_ENTERED")
        print(f"[SheetsClient] {len(report_data)} filas exportadas a '{sheet_name}'")
