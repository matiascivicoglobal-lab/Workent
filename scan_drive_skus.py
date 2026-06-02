#!/usr/bin/env python3
"""
Recursively scans CATEGORÍAS MATIAS PM on Google Drive and builds
a SKU -> first image fileId map.
"""

import json
import ssl
import sys
import httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

CREDENTIALS_PATH = "/home/user/Workent/credentials/service_account.json"
ROOT_FOLDER_ID = "1nlN8JWwSp9dPNcrKX6qZOqOIzn8DDDY5"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

FOLDER_MIME = "application/vnd.google-apps.folder"


def build_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    # Disable SSL verification to handle self-signed cert in chain
    http = httplib2.Http(disable_ssl_certificate_validation=True)
    authed_http = AuthorizedHttp(creds, http=http)
    return build("drive", "v3", http=authed_http, cache_discovery=False)


def list_children(service, folder_id):
    """Return all children (files + folders) of a given folder."""
    results = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=500,
                pageToken=page_token,
            )
            .execute()
        )
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def is_image(item):
    mime = item.get("mimeType", "")
    name = item.get("name", "").lower()
    if mime in IMAGE_MIMES:
        return True
    if any(name.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return True
    return False


def is_folder(item):
    return item.get("mimeType") == FOLDER_MIME


def is_sku_folder(folder_name):
    """
    Heuristic: a SKU folder name typically:
    - Is uppercase-heavy
    - Contains letters + possibly hyphens, numbers
    - Doesn't look like a pure category name (we treat everything as potential SKU)
    Actually we just collect image first-file for any folder that CONTAINS images.
    So we don't need a strict filter here — we collect any folder with images.
    """
    return True  # accept all; filter later by "has images"


def scan_folder(service, folder_id, folder_name, depth, max_depth=4):
    """
    Recursively scan folder up to max_depth.
    Returns a dict: {sku_name_upper: first_image_file_id}
    """
    if depth > max_depth:
        return {}

    children = list_children(service, folder_id)

    images = [c for c in children if not is_folder(c) and is_image(c)]
    subfolders = [c for c in children if is_folder(c)]

    sku_map = {}

    # If this folder has images, treat it as a SKU folder
    if images:
        sku_key = folder_name.strip().upper()
        # Use the first image found (stable order from API)
        sku_map[sku_key] = images[0]["id"]
        # Log progress
        print(
            f"  [depth={depth}] SKU found: {sku_key!r} -> {images[0]['id']} "
            f"(file: {images[0]['name']!r})",
            file=sys.stderr,
        )

    # Always recurse into subfolders
    for sf in subfolders:
        child_map = scan_folder(service, sf["id"], sf["name"], depth + 1, max_depth)
        # Merge; first occurrence wins on collision
        for k, v in child_map.items():
            if k not in sku_map:
                sku_map[k] = v

    return sku_map


def main():
    print("Building Drive service...", file=sys.stderr)
    service = build_service()

    print(f"Starting scan from root: {ROOT_FOLDER_ID}", file=sys.stderr)

    # List Level 1 (category folders)
    level1 = list_children(service, ROOT_FOLDER_ID)
    print(f"Level-1 items: {len(level1)}", file=sys.stderr)
    for item in level1:
        tag = "[FOLDER]" if is_folder(item) else "[FILE  ]"
        print(f"  {tag} {item['name']!r} ({item['id']})", file=sys.stderr)

    sku_map = {}

    for item in level1:
        if is_folder(item):
            print(f"\nScanning category: {item['name']!r}", file=sys.stderr)
            child_map = scan_folder(service, item["id"], item["name"], depth=1)
            for k, v in child_map.items():
                if k not in sku_map:
                    sku_map[k] = v
        elif is_image(item):
            # Image directly in root — unlikely but handle it
            sku_map[item["name"].upper()] = item["id"]

    print("\n\n=== RESULT ===", file=sys.stderr)
    print(f"Total SKUs found: {len(sku_map)}", file=sys.stderr)

    # Print the JSON result to stdout
    print(json.dumps(sku_map, indent=2, ensure_ascii=False))
    print(f"\n# Total SKUs: {len(sku_map)}", file=sys.stdout)


if __name__ == "__main__":
    main()
