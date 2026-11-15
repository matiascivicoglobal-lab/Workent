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


def guardar_clave(ruta: Path, clave: str, valor) -> bool:
    """Escribe `clave=valor` en un .env sin tocar el resto del archivo.

    Reemplaza también la versión comentada (`# CLAVE=`), que es la trampa
    clásica: pegás el valor en una línea que empieza con # y no toma efecto.
    """
    linea = f"{clave}={valor}"
    if not ruta.exists():
        ruta.write_text(linea + "\n", encoding="utf-8")
        return True

    patron = re.compile(rf"^\s*#?\s*{re.escape(clave)}\s*=.*$", flags=re.M)
    texto = ruta.read_text(encoding="utf-8")
    if patron.search(texto):
        # La primera aparición se reemplaza; las demás (duplicados o
        # comentadas) se eliminan, para que no quede una pisando a la otra.
        reemplazadas = {"hecho": False}

        def _sub(_m):
            if reemplazadas["hecho"]:
                return "\x00BORRAR\x00"
            reemplazadas["hecho"] = True
            return linea

        texto = patron.sub(_sub, texto)
        texto = "\n".join(l for l in texto.splitlines() if l != "\x00BORRAR\x00")
        if not texto.endswith("\n"):
            texto += "\n"
    else:
        texto = texto.rstrip("\n") + f"\n{linea}\n"

    ruta.write_text(texto, encoding="utf-8")
    return True


def guardar_en_env(ruta: Path, chat_id) -> bool:
    """Atajo histórico: guarda el chat_id."""
    return guardar_clave(ruta, "TELEGRAM_CHAT_ID", chat_id)
