"""Navegador headless (Playwright) para los portales con anti-bot.

Se importa en forma perezosa: el radar funciona sin Playwright, solo que
quedan deshabilitadas las fuentes que lo necesitan.

Instalación:  pip install playwright && playwright install chromium
"""

from __future__ import annotations

import logging
import os
import random
import time
from pathlib import Path

log = logging.getLogger("radar.navegador")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Recursos que no aportan nada al scraping y cuestan mucho tiempo.
BLOQUEAR = {"image", "media", "font"}


def disponible() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


class Navegador:
    def __init__(self, headless: bool = True, perfil: str | Path | None = None,
                 estado_sesion: str | Path | None = None, demora: float = 2.0):
        if not disponible():
            raise RuntimeError(
                "Playwright no está instalado.\n"
                "  pip install playwright && playwright install chromium\n"
                "O desactivá las fuentes con 'navegador: true' en config.yaml")
        self.headless = headless
        self.perfil = Path(perfil) if perfil else None
        self.estado_sesion = Path(estado_sesion) if estado_sesion else None
        self.demora = demora
        self._pw = None
        self._browser = None
        self._ctx = None

    # ------------------------------------------------------------------
    def abrir(self):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        args = ["--no-sandbox", "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"]
        opciones_ctx = {
            "user_agent": UA,
            "locale": "es-AR",
            "timezone_id": "America/Argentina/Buenos_Aires",
            "viewport": {"width": 1366, "height": 850},
        }
        ejecutable = os.getenv("CHROMIUM_PATH")
        lanzar = {"headless": self.headless, "args": args}
        if ejecutable:
            lanzar["executable_path"] = ejecutable

        if self.perfil:                     # perfil persistente (sesiones logueadas)
            self.perfil.mkdir(parents=True, exist_ok=True)
            self._ctx = self._pw.chromium.launch_persistent_context(
                str(self.perfil), **lanzar, **opciones_ctx)
        else:
            self._browser = self._pw.chromium.launch(**lanzar)
            if self.estado_sesion and self.estado_sesion.exists():
                opciones_ctx["storage_state"] = str(self.estado_sesion)
            self._ctx = self._browser.new_context(**opciones_ctx)

        # Disimula el marcador de automatización que miran los anti-bot.
        self._ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "window.chrome={runtime:{}};"
            "Object.defineProperty(navigator,'languages',{get:()=>['es-AR','es']});")
        self._ctx.route("**/*", self._filtrar)
        return self

    @staticmethod
    def _filtrar(ruta, pedido):
        if pedido.resource_type in BLOQUEAR:
            ruta.abort()
        else:
            ruta.continue_()

    def cerrar(self):
        for obj in (self._ctx, self._browser, self._pw):
            try:
                if obj:
                    (obj.stop if hasattr(obj, "stop") else obj.close)()
            except Exception:                     # noqa: BLE001
                pass
        self._ctx = self._browser = self._pw = None

    def __enter__(self):
        return self.abrir()

    def __exit__(self, *_):
        self.cerrar()

    # ------------------------------------------------------------------
    def html(self, url: str, espera: str | None = None, scroll: bool = True,
             timeout: int = 45000) -> str | None:
        if not self._ctx:
            self.abrir()
        pagina = self._ctx.new_page()
        try:
            time.sleep(self.demora + random.uniform(0, 1.5))
            pagina.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if espera:
                try:
                    pagina.wait_for_selector(espera, timeout=15000)
                except Exception:                 # noqa: BLE001
                    log.debug("  no apareció '%s' en %s", espera, url)
            if scroll:
                # Muchos listados cargan las tarjetas al hacer scroll.
                for _ in range(3):
                    pagina.mouse.wheel(0, 2200)
                    pagina.wait_for_timeout(600)
            contenido = pagina.content()
            if _es_muro(contenido):
                log.warning("  %s devolvió un muro anti-bot (Cloudflare/captcha)", url)
                return None
            return contenido
        except Exception as e:                    # noqa: BLE001
            log.warning("  navegador falló en %s: %s", url, e)
            return None
        finally:
            pagina.close()

    def guardar_sesion(self, destino: str | Path) -> None:
        if self._ctx:
            self._ctx.storage_state(path=str(destino))


def _es_muro(html: str) -> bool:
    bajo = html[:4000].lower()
    marcas = ("just a moment", "checking your browser", "cf-browser-verification",
              "captcha-delivery", "access denied", "unusual traffic")
    return any(m in bajo for m in marcas)
