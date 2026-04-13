import os
import json
from dotenv import load_dotenv

load_dotenv()


def get_service_account_credentials():
    """
    Returns the service account credentials dict.
    Supports both a JSON file path and an inline JSON string (for cloud deploys).
    """
    inline_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if inline_json:
        return json.loads(inline_json)

    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Service account file not found: '{file_path}'\n"
            "Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON in your .env"
        )
    with open(file_path) as f:
        return json.load(f)


DEFAULT_SPREADSHEET_ID = os.getenv("DEFAULT_SPREADSHEET_ID", "")
DEFAULT_SHEET_NAME = os.getenv("DEFAULT_SHEET_NAME", "Sheet1")
