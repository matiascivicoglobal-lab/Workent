"""
Google Drive client.
Soporta: listar archivos, leer metadatos, descargar contenido y exportar Google Docs/Sheets.
Autenticación via Service Account (comparte credenciales con SheetsClient).
"""

import io
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from google_auth_httplib2 import AuthorizedHttp

from config import get_service_account_credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# MIME types de exportación para archivos nativos de Google
EXPORT_MIME = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}


class DriveClient:
    def __init__(self):
        creds_dict = get_service_account_credentials()
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        http = httplib2.Http(disable_ssl_certificate_validation=True)
        authed_http = AuthorizedHttp(creds, http=http)
        self._service = build("drive", "v3", http=authed_http)

    # ------------------------------------------------------------------
    # Listar
    # ------------------------------------------------------------------

    def list_files(self, query: str = "", folder_id: str = "", max_results: int = 100) -> list[dict]:
        """
        Lista archivos en Drive.

        Args:
            query:      Filtro en Drive Query Language, e.g. "name contains 'reporte'".
            folder_id:  Si se pasa, limita la búsqueda a esa carpeta.
            max_results: Cantidad máxima de resultados.

        Returns:
            Lista de dicts con id, name, mimeType, modifiedTime.
        """
        parts = []
        if folder_id:
            parts.append(f"'{folder_id}' in parents")
        if query:
            parts.append(query)
        parts.append("trashed = false")

        q = " and ".join(parts)

        results = (
            self._service.files()
            .list(
                q=q,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, size)",
            )
            .execute()
        )
        return results.get("files", [])

    # ------------------------------------------------------------------
    # Metadatos
    # ------------------------------------------------------------------

    def get_metadata(self, file_id: str) -> dict:
        """Devuelve los metadatos completos de un archivo."""
        return (
            self._service.files()
            .get(fileId=file_id, fields="id, name, mimeType, modifiedTime, size, parents")
            .execute()
        )

    # ------------------------------------------------------------------
    # Leer contenido
    # ------------------------------------------------------------------

    def read_file(self, file_id: str) -> bytes:
        """
        Descarga el contenido binario de un archivo.
        Para archivos nativos de Google (Docs, Sheets, etc.) usa read_text() en su lugar.
        """
        request = self._service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()

    def read_text(self, file_id: str, encoding: str = "utf-8") -> str:
        """
        Lee un archivo como texto.
        - Archivos nativos de Google: se exportan automáticamente (Doc→txt, Sheet→csv).
        - Otros archivos (txt, csv, json, etc.): se descargan directamente.
        """
        meta = self.get_metadata(file_id)
        mime = meta.get("mimeType", "")

        if mime in EXPORT_MIME:
            export_mime = EXPORT_MIME[mime]
            request = self._service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            request = self._service.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buf.getvalue().decode(encoding)
