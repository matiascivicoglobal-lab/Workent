"""Ayuda para terminar el alta de Telegram: encontrar el chat_id.

Telegram no te dice cuál es tu chat_id: hay que escribirle al bot y después
leerlo de getUpdates. Esto lo hace por vos y lo guarda en el .env.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import httpx

log = logging.getLogger("radar.telegram")


def enmascarar(token: str) -> str:
    """Nunca imprimir el token entero."""
    if not token or len(token) < 12:
        return "(vacío)"
    return f"{token[:10]}…{token[-4:]}"


def extraer_chats(datos: dict) -> list[dict]:
    """Saca los chats distintos de una respuesta de getUpdates."""
    vistos, chats = set(), []
    for upd in (datos or {}).get("result", []) or []:
        msg = (upd.get("message") or upd.get("channel_post")
               or upd.get("edited_message") or {})
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        if cid is None or cid in vistos:
            continue
        vistos.add(cid)
        nombre = (chat.get("title")
                  or " ".join(filter(None, [chat.get("first_name"),
                                            chat.get("last_name")]))
                  or chat.get("username") or "sin nombre")
        chats.append({"id": cid, "nombre": nombre, "tipo": chat.get("type", "?")})
    return chats


def chats_del_bot(token: str) -> tuple[list[dict], str]:
    """Devuelve (chats encontrados, mensaje de error)."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        r = httpx.get(url, timeout=25)
    except httpx.HTTPError as e:
        return [], (f"No pude hablar con Telegram: {e}. "
                    "Revisá tu conexión o si hay un proxy/firewall en el medio.")

    if r.status_code == 401:
        return [], ("Telegram rechazó el token (401). Revisá TELEGRAM_TOKEN en el .env; "
                    "si lo regeneraste con /revoke en BotFather, pegá el nuevo.")
    if r.status_code != 200:
        return [], f"Telegram respondió {r.status_code}: {r.text[:200]}"

    try:
        datos = r.json()
    except ValueError:
        return [], "Telegram devolvió algo que no es JSON"
    if not datos.get("ok"):
        return [], f"Telegram devolvió un error: {datos.get('description', datos)}"

    return extraer_chats(datos), ""


def guardar_en_env(ruta: Path, chat_id) -> bool:
    """Escribe TELEGRAM_CHAT_ID en el .env sin tocar el resto."""
    if not ruta.exists():
        ruta.write_text(f"TELEGRAM_CHAT_ID={chat_id}\n", encoding="utf-8")
        return True
    texto = ruta.read_text(encoding="utf-8")
    linea = f"TELEGRAM_CHAT_ID={chat_id}"
    if re.search(r"^\s*TELEGRAM_CHAT_ID\s*=.*$", texto, flags=re.M):
        texto = re.sub(r"^\s*TELEGRAM_CHAT_ID\s*=.*$", linea, texto, count=1, flags=re.M)
    else:
        texto = texto.rstrip("\n") + f"\n{linea}\n"
    ruta.write_text(texto, encoding="utf-8")
    return True
