"""Persistencia en SQLite: avisos, historial de precios y alertas enviadas.

El historial de precios es la pieza clave: detectar que un aviso BAJÓ de
precio vale tanto como encontrarlo barato de entrada.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .modelo import Aviso
from .util import ahora

ESQUEMA = """
CREATE TABLE IF NOT EXISTS avisos (
    id             TEXT PRIMARY KEY,
    fuente         TEXT NOT NULL,
    id_externo     TEXT NOT NULL,
    clave_dedupe   TEXT,
    url            TEXT,
    titulo         TEXT,
    barrio         TEXT,
    direccion      TEXT,
    precio         REAL,
    moneda         TEXT,
    precio_usd     REAL,
    expensas_ars   REAL,
    m2_totales     REAL,
    m2_cubiertos   REAL,
    ambientes      INTEGER,
    dormitorios    INTEGER,
    banios         INTEGER,
    antiguedad     INTEGER,
    piso           TEXT,
    tipo           TEXT,
    publicado      TEXT,
    imagen         TEXT,
    descripcion    TEXT,
    extra          TEXT,
    visto_primero  TEXT,
    visto_ultimo   TEXT,
    activo         INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_avisos_barrio ON avisos(barrio);
CREATE INDEX IF NOT EXISTS ix_avisos_dedupe ON avisos(clave_dedupe);
CREATE INDEX IF NOT EXISTS ix_avisos_visto  ON avisos(visto_ultimo);

CREATE TABLE IF NOT EXISTS historial_precios (
    aviso_id   TEXT NOT NULL,
    ts         TEXT NOT NULL,
    precio_usd REAL,
    PRIMARY KEY (aviso_id, ts)
);

CREATE TABLE IF NOT EXISTS alertas (
    aviso_id TEXT NOT NULL,
    ts       TEXT NOT NULL,
    tipo     TEXT NOT NULL,      -- nueva | baja_precio
    puntaje  REAL,
    detalle  TEXT,
    PRIMARY KEY (aviso_id, tipo, ts)
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    fecha   TEXT PRIMARY KEY,
    tipo    TEXT,
    usd_ars REAL
);

CREATE TABLE IF NOT EXISTS corridas (
    ts        TEXT PRIMARY KEY,
    fuente    TEXT,
    hallados  INTEGER,
    nuevos    INTEGER,
    error     TEXT
);
"""


class Almacen:
    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.ruta, timeout=30)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.executescript(ESQUEMA)
        self.con.commit()

    def cerrar(self) -> None:
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()

    @contextmanager
    def tx(self):
        try:
            yield self.con
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    # ------------------------------------------------------------------
    # Avisos
    # ------------------------------------------------------------------
    def guardar(self, aviso: Aviso) -> dict:
        """Inserta o actualiza. Devuelve qué cambió:
        {'nuevo': bool, 'precio_anterior': float|None, 'variacion': float|None}
        """
        ts = ahora().isoformat()
        previo = self.con.execute(
            "SELECT precio_usd, visto_primero FROM avisos WHERE id = ?", (aviso.id,)
        ).fetchone()

        datos = aviso.a_dict()
        datos["extra"] = json.dumps(aviso.extra, ensure_ascii=False, default=str)
        datos["clave_dedupe"] = aviso.clave_dedupe()
        datos["visto_ultimo"] = ts
        datos["visto_primero"] = previo["visto_primero"] if previo else ts
        datos["activo"] = 1
        datos.pop("id", None)

        columnas = [c for c in datos if c in _COLUMNAS_AVISOS]
        valores = [datos[c] for c in columnas]

        with self.tx() as con:
            if previo:
                sets = ", ".join(f"{c} = ?" for c in columnas)
                con.execute(f"UPDATE avisos SET {sets} WHERE id = ?", [*valores, aviso.id])
            else:
                cols = ", ".join(["id", *columnas])
                marcas = ", ".join(["?"] * (len(columnas) + 1))
                con.execute(f"INSERT INTO avisos ({cols}) VALUES ({marcas})",
                            [aviso.id, *valores])
            if aviso.precio_usd:
                con.execute(
                    "INSERT OR IGNORE INTO historial_precios (aviso_id, ts, precio_usd) "
                    "VALUES (?, ?, ?)", (aviso.id, ts, aviso.precio_usd))

        precio_anterior = previo["precio_usd"] if previo else None
        variacion = None
        if precio_anterior and aviso.precio_usd and precio_anterior > 0:
            variacion = (aviso.precio_usd - precio_anterior) / precio_anterior
        return {"nuevo": previo is None, "precio_anterior": precio_anterior,
                "variacion": variacion}

    def obtener(self, aviso_id: str) -> Aviso | None:
        fila = self.con.execute("SELECT * FROM avisos WHERE id = ?", (aviso_id,)).fetchone()
        return Aviso.desde_dict(dict(fila)) if fila else None

    def primera_vez(self, aviso_id: str):
        """Desde cuándo el radar ve este aviso (sirve cuando el portal no
        publica la fecha de alta)."""
        f = self.con.execute("SELECT visto_primero FROM avisos WHERE id = ?",
                             (aviso_id,)).fetchone()
        return f["visto_primero"] if f else None

    def avisos(self, barrio: str | None = None, dias: int | None = None,
               solo_activos: bool = True) -> list[Aviso]:
        sql = "SELECT * FROM avisos WHERE 1=1"
        args: list = []
        if barrio:
            sql += " AND lower(barrio) = ?"
            args.append(barrio.strip().lower())
        if dias:
            corte = (ahora() - timedelta(days=dias)).isoformat()
            sql += " AND visto_ultimo >= ?"
            args.append(corte)
        if solo_activos:
            sql += " AND activo = 1"
        return [Aviso.desde_dict(dict(f)) for f in self.con.execute(sql, args)]

    def marcar_inactivos(self, dias: int = 21) -> int:
        """Un aviso que no vemos hace semanas probablemente se vendió o se bajó."""
        corte = (ahora() - timedelta(days=dias)).isoformat()
        with self.tx() as con:
            cur = con.execute(
                "UPDATE avisos SET activo = 0 WHERE activo = 1 AND visto_ultimo < ?",
                (corte,))
        return cur.rowcount

    def historial(self, aviso_id: str) -> list[tuple[str, float]]:
        filas = self.con.execute(
            "SELECT ts, precio_usd FROM historial_precios WHERE aviso_id = ? ORDER BY ts",
            (aviso_id,)).fetchall()
        return [(f["ts"], f["precio_usd"]) for f in filas]

    def baja_de_precio(self, aviso_id: str) -> dict | None:
        """Mayor caída registrada respecto del precio más alto histórico."""
        h = self.historial(aviso_id)
        if len(h) < 2:
            return None
        precios = [p for _, p in h if p]
        if len(precios) < 2:
            return None
        maximo, actual = max(precios), precios[-1]
        if actual >= maximo:
            return None
        idx = precios.index(maximo)
        return {
            "desde": maximo,
            "hasta": actual,
            "pct": (maximo - actual) / maximo,
            "dias": max(0, (_fecha(h[-1][0]) - _fecha(h[idx][0])).days),
        }

    # ------------------------------------------------------------------
    # Dedupe entre portales
    # ------------------------------------------------------------------
    def duplicados_de(self, aviso: Aviso) -> list[str]:
        clave = aviso.clave_dedupe()
        if clave == aviso.id:
            return []
        filas = self.con.execute(
            "SELECT id FROM avisos WHERE clave_dedupe = ? AND id != ?",
            (clave, aviso.id)).fetchall()
        return [f["id"] for f in filas]

    # ------------------------------------------------------------------
    # Alertas
    # ------------------------------------------------------------------
    def ya_alertado(self, aviso_id: str, tipo: str = "nueva") -> bool:
        f = self.con.execute(
            "SELECT 1 FROM alertas WHERE aviso_id = ? AND tipo = ? LIMIT 1",
            (aviso_id, tipo)).fetchone()
        return f is not None

    def registrar_alerta(self, aviso_id: str, tipo: str, puntaje: float,
                         detalle: str = "") -> None:
        with self.tx() as con:
            con.execute(
                "INSERT OR REPLACE INTO alertas (aviso_id, ts, tipo, puntaje, detalle) "
                "VALUES (?, ?, ?, ?, ?)",
                (aviso_id, ahora().isoformat(), tipo, puntaje, detalle))

    def alertas_recientes(self, horas: int = 24) -> list[sqlite3.Row]:
        corte = (ahora() - timedelta(hours=horas)).isoformat()
        return self.con.execute(
            "SELECT a.*, v.titulo, v.barrio, v.precio_usd, v.url "
            "FROM alertas a LEFT JOIN avisos v ON v.id = a.aviso_id "
            "WHERE a.ts >= ? ORDER BY a.puntaje DESC", (corte,)).fetchall()

    # ------------------------------------------------------------------
    # Cotización y corridas
    # ------------------------------------------------------------------
    def guardar_cotizacion(self, tipo: str, valor: float) -> None:
        hoy = ahora().date().isoformat()
        with self.tx() as con:
            con.execute("INSERT OR REPLACE INTO cotizaciones (fecha, tipo, usd_ars) "
                        "VALUES (?, ?, ?)", (hoy, tipo, valor))

    def cotizacion_de_hoy(self) -> float | None:
        hoy = ahora().date().isoformat()
        f = self.con.execute("SELECT usd_ars FROM cotizaciones WHERE fecha = ?",
                             (hoy,)).fetchone()
        return f["usd_ars"] if f else None

    def ultima_cotizacion(self) -> float | None:
        f = self.con.execute(
            "SELECT usd_ars FROM cotizaciones ORDER BY fecha DESC LIMIT 1").fetchone()
        return f["usd_ars"] if f else None

    def registrar_corrida(self, fuente: str, hallados: int, nuevos: int,
                          error: str = "") -> None:
        with self.tx() as con:
            con.execute(
                "INSERT OR REPLACE INTO corridas (ts, fuente, hallados, nuevos, error) "
                "VALUES (?, ?, ?, ?, ?)",
                (ahora().isoformat(), fuente, hallados, nuevos, error))

    def ultima_corrida(self, fuente: str):
        """Cuándo corrió por última vez una fuente (para limitar su frecuencia)."""
        f = self.con.execute(
            "SELECT ts FROM corridas WHERE fuente = ? ORDER BY ts DESC LIMIT 1",
            (fuente,)).fetchone()
        return f["ts"] if f else None

    def nuevos_desde(self, horas: int = 24) -> int:
        corte = (ahora() - timedelta(hours=horas)).isoformat()
        f = self.con.execute(
            "SELECT COUNT(*) n FROM avisos WHERE visto_primero >= ?", (corte,)).fetchone()
        return f["n"] or 0

    def resumen(self) -> dict:
        c = self.con.execute(
            "SELECT COUNT(*) n, SUM(activo) activos FROM avisos").fetchone()
        por_barrio = self.con.execute(
            "SELECT barrio, COUNT(*) n FROM avisos WHERE activo = 1 GROUP BY barrio"
        ).fetchall()
        return {
            "total": c["n"] or 0,
            "activos": c["activos"] or 0,
            "por_barrio": {f["barrio"]: f["n"] for f in por_barrio},
        }


_COLUMNAS_AVISOS = {
    "fuente", "id_externo", "clave_dedupe", "url", "titulo", "barrio", "direccion",
    "precio", "moneda", "precio_usd", "expensas_ars", "m2_totales", "m2_cubiertos",
    "ambientes", "dormitorios", "banios", "antiguedad", "piso", "tipo", "publicado",
    "imagen", "descripcion", "extra", "visto_primero", "visto_ultimo", "activo",
}


def _fecha(ts: str) -> datetime:
    try:
        d = datetime.fromisoformat(ts)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return ahora()
