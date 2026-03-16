# -*- coding: utf-8 -*-
"""
aura/database.py
Base de datos SQLite para Aura: Escudo Etico.
"""
import sqlite3
import os
from datetime import datetime, date

_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "aura_data.db")
)


def _conn():
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def inicializar():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS detecciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            texto       TEXT    NOT NULL,
            nivel       TEXT    NOT NULL,
            score_ia    REAL    NOT NULL,
            fuente      TEXT    NOT NULL,
            razon       TEXT    DEFAULT '',
            sugerencia  TEXT    DEFAULT '',
            sitio       TEXT    DEFAULT '',
            puntos_rest INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS score_diario (
            fecha       TEXT    PRIMARY KEY,
            score       INTEGER NOT NULL DEFAULT 100,
            detecciones INTEGER NOT NULL DEFAULT 0,
            nivel_dia   TEXT    NOT NULL DEFAULT 'Excelente'
        );
        CREATE TABLE IF NOT EXISTS decisiones (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            deteccion_id  INTEGER,
            fecha         TEXT    NOT NULL,
            decision      TEXT    NOT NULL,
            tiempo_ms     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sitios_bloq (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_ini   TEXT    NOT NULL,
            fecha_fin   TEXT    DEFAULT '',
            sitio       TEXT    NOT NULL,
            razon       TEXT    DEFAULT '',
            activo      INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS config_store (
            clave TEXT PRIMARY KEY,
            valor TEXT DEFAULT ''
        );
        """)
    _asegurar_score_hoy()


def _asegurar_score_hoy():
    hoy = date.today().isoformat()
    with _conn() as con:
        existe = con.execute(
            "SELECT 1 FROM score_diario WHERE fecha=?", (hoy,)
        ).fetchone()
        if not existe:
            ayer = con.execute(
                "SELECT score FROM score_diario ORDER BY fecha DESC LIMIT 1"
            ).fetchone()
            score_ini = ayer["score"] if ayer else 100
            con.execute(
                "INSERT INTO score_diario(fecha,score) VALUES(?,?)",
                (hoy, score_ini)
            )


def _nivel_score(s):
    if s >= 80: return "Excelente"
    if s >= 60: return "Bueno"
    if s >= 40: return "En riesgo"
    if s >= 20: return "Critico"
    return "Muy critico"


def get_score_hoy():
    _asegurar_score_hoy()
    hoy = date.today().isoformat()
    with _conn() as con:
        row = con.execute(
            "SELECT score FROM score_diario WHERE fecha=?", (hoy,)
        ).fetchone()
    return row["score"] if row else 100


def get_score_historico(dias=7):
    with _conn() as con:
        rows = con.execute(
            "SELECT fecha,score,detecciones,nivel_dia "
            "FROM score_diario ORDER BY fecha DESC LIMIT ?", (dias,)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def bajar_score(puntos, razon=""):
    _asegurar_score_hoy()
    hoy = date.today().isoformat()
    with _conn() as con:
        actual = con.execute(
            "SELECT score FROM score_diario WHERE fecha=?", (hoy,)
        ).fetchone()
        nuevo = max(0, actual["score"] - puntos)
        con.execute(
            "UPDATE score_diario SET score=?, detecciones=detecciones+1, nivel_dia=? WHERE fecha=?",
            (nuevo, _nivel_score(nuevo), hoy)
        )
    return nuevo


def registrar_deteccion(texto, nivel, score_ia, fuente,
                         razon="", sugerencia="", sitio="", puntos_rest=0):
    fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO detecciones(fecha,texto,nivel,score_ia,fuente,razon,sugerencia,sitio,puntos_rest)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (fecha, texto[:500], nivel, score_ia, fuente, razon, sugerencia, sitio, puntos_rest)
        )
    return cur.lastrowid


def get_detecciones(limite=50, solo_hoy=False):
    hoy = date.today().isoformat()
    with _conn() as con:
        if solo_hoy:
            rows = con.execute(
                "SELECT * FROM detecciones WHERE fecha LIKE ? ORDER BY fecha DESC LIMIT ?",
                (hoy+"%", limite)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM detecciones ORDER BY fecha DESC LIMIT ?", (limite,)
            ).fetchall()
    return [dict(r) for r in rows]


def get_stats_hoy():
    hoy = date.today().isoformat()
    with _conn() as con:
        total    = con.execute("SELECT COUNT(*) n FROM detecciones WHERE fecha LIKE ?", (hoy+"%",)).fetchone()["n"]
        criticos = con.execute("SELECT COUNT(*) n FROM detecciones WHERE fecha LIKE ? AND nivel='CRITICO'", (hoy+"%",)).fetchone()["n"]
        editados = con.execute(
            "SELECT COUNT(*) n FROM decisiones d JOIN detecciones det ON d.deteccion_id=det.id "
            "WHERE det.fecha LIKE ? AND d.decision='editar'", (hoy+"%",)
        ).fetchone()["n"]
    return {"total": total, "criticos": criticos, "editados": editados, "score": get_score_hoy()}


def registrar_decision(deteccion_id, decision, tiempo_ms=0):
    fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
    with _conn() as con:
        con.execute(
            "INSERT INTO decisiones(deteccion_id,fecha,decision,tiempo_ms) VALUES(?,?,?,?)",
            (deteccion_id, fecha, decision, tiempo_ms)
        )


def registrar_sitio_bloqueado(sitio, razon=""):
    fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
    with _conn() as con:
        con.execute("INSERT INTO sitios_bloq(fecha_ini,sitio,razon) VALUES(?,?,?)", (fecha,sitio,razon))


def desbloquear_sitio_db(sitio):
    fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
    with _conn() as con:
        con.execute(
            "UPDATE sitios_bloq SET activo=0,fecha_fin=? WHERE sitio=? AND activo=1",
            (fecha, sitio)
        )


def get_sitios_bloqueados(limite=20):
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM sitios_bloq ORDER BY fecha_ini DESC LIMIT ?", (limite,)
        ).fetchall()
    return [dict(r) for r in rows]


def set_config(clave, valor):
    with _conn() as con:
        con.execute("INSERT OR REPLACE INTO config_store(clave,valor) VALUES(?,?)", (clave, valor))


def get_config(clave, default=""):
    with _conn() as con:
        row = con.execute("SELECT valor FROM config_store WHERE clave=?", (clave,)).fetchone()
    return row["valor"] if row else default


def limpiar_todo():
    with _conn() as con:
        con.executescript("""
            DELETE FROM detecciones;
            DELETE FROM score_diario;
            DELETE FROM decisiones;
            DELETE FROM sitios_bloq;
        """)
    _asegurar_score_hoy()
