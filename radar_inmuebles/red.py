"""Cliente HTTP con headers de navegador real, reintentos y rate limiting."""

from __future__ import annotations

import logging
import random
import time

import httpx

log = logging.getLogger("radar.red")

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


def cabeceras(referer: str | None = None) -> dict[str, str]:
    h = {
        "User-Agent": random.choice(UA),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.6",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h


class Cliente:
    """Un cliente por corrida. Mantiene cookies y espacia los pedidos."""

    def __init__(self, demora: float = 2.5, timeout: float = 30,
                 reintentos: int = 3, proxy: str | None = None,
                 max_fallos: int = 4):
        self.demora = demora
        self.reintentos = reintentos
        # Cortacircuitos: si un portal nos rechaza una y otra vez, dejamos de
        # insistir en esta corrida. Evita esperas larguísimas y castigos de IP.
        self.max_fallos = max_fallos
        self._fallos: dict[str, int] = {}
        self._ultimo: dict[str, float] = {}
        self.http = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=cabeceras(),
            proxy=proxy,
            http2=False,
        )

    def _esperar(self, host: str) -> None:
        ultimo = self._ultimo.get(host)
        if ultimo:
            falta = self.demora + random.uniform(0, self.demora * 0.4) - (time.time() - ultimo)
            if falta > 0:
                time.sleep(falta)
        self._ultimo[host] = time.time()

    def get(self, url: str, *, referer: str | None = None,
            params: dict | None = None, headers: dict | None = None,
            json_esperado: bool = False):
        host = httpx.URL(url).host or url
        if self._fallos.get(host, 0) >= self.max_fallos:
            log.debug("  %s sigue sin responder, lo salteo en esta corrida", host)
            return None
        ultimo_error: Exception | None = None

        for intento in range(1, self.reintentos + 1):
            self._esperar(host)
            h = cabeceras(referer)
            if json_esperado:
                h["Accept"] = "application/json, text/plain, */*"
                h["Sec-Fetch-Dest"] = "empty"
                h["Sec-Fetch-Mode"] = "cors"
            h.update(headers or {})
            try:
                r = self.http.get(url, params=params, headers=h)
            except httpx.HTTPError as e:
                ultimo_error = e
                log.debug("  %s intento %d falló: %s", host, intento, e)
                time.sleep(2 ** intento)
                continue

            if r.status_code == 200:
                self._fallos[host] = 0
                return r
            if r.status_code in (403, 429, 503):
                log.warning("  %s respondió %d (bloqueo/anti-bot) intento %d/%d",
                            host, r.status_code, intento, self.reintentos)
                time.sleep(3 * intento + random.uniform(0, 3))
                ultimo_error = httpx.HTTPStatusError(
                    f"HTTP {r.status_code}", request=r.request, response=r)
                continue
            if 400 <= r.status_code < 500:
                log.debug("  %s respondió %d, no reintento", url, r.status_code)
                return None
            ultimo_error = httpx.HTTPStatusError(
                f"HTTP {r.status_code}", request=r.request, response=r)
            time.sleep(2 ** intento)

        self._fallos[host] = self._fallos.get(host, 0) + 1
        if self._fallos[host] == self.max_fallos:
            log.warning("  %s falló %d veces seguidas: lo dejo afuera de esta corrida",
                        host, self.max_fallos)
        else:
            log.warning("  No pude traer %s (%s)", url, ultimo_error)
        return None

    def host_caido(self, url: str) -> bool:
        host = httpx.URL(url).host or url
        return self._fallos.get(host, 0) >= self.max_fallos

    def html(self, url: str, **kw) -> str | None:
        r = self.get(url, **kw)
        return r.text if r is not None else None

    def json(self, url: str, **kw):
        r = self.get(url, json_esperado=True, **kw)
        if r is None:
            return None
        try:
            return r.json()
        except ValueError:
            log.debug("  %s no devolvió JSON válido", url)
            return None

    def cerrar(self) -> None:
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()
