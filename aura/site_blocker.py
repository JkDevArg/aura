# -*- coding: utf-8 -*-
"""
site_blocker.py
Bloqueo de sitios web editando el archivo hosts de Windows.
Requiere permisos de Administrador.

Logica:
  - Se registra cada deteccion por sitio
  - A la 3ra deteccion en el mismo sitio: se bloquea 3 minutos
  - Despues de 3 minutos: se desbloquea automaticamente
"""
import ctypes
import os
import time

from aura.config import C
from aura.logger import log

# ── Constantes ────────────────────────────────────────────
HOSTS_PATH          = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP         = "127.0.0.1"
MARCA               = "# AuraEscudoEtico"
DETECCIONES_LIMITE  = 3
SEGUNDOS_BLOQUEO    = 180   # 3 minutos

SITIOS_MONITOREADOS = [
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "linkedin.com",
]

# ── Estado interno ────────────────────────────────────────
_conteo:    dict[str, int]   = {}   # {sitio: n_detecciones}
_bloqueados: dict[str, float] = {}  # {sitio: timestamp_desbloqueo}


# ── Utilidades ────────────────────────────────────────────

def es_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def sitio_activo() -> str | None:
    """Detecta el sitio que tiene el foco via titulo de ventana."""
    try:
        hwnd   = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf    = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        titulo = buf.value.lower()
        for sitio in SITIOS_MONITOREADOS:
            nombre = sitio.replace(".com", "").replace(".", "")
            if nombre in titulo:
                return sitio
    except Exception:
        pass
    return None


# ── Registro de detecciones ───────────────────────────────

def registrar_deteccion(sitio: str = None) -> tuple[int, bool, int]:
    """
    Registra una deteccion para el sitio indicado (o el activo).
    Retorna: (n_total, fue_bloqueado, segundos_de_bloqueo)
    """
    if not sitio:
        sitio = sitio_activo() or "desconocido"

    _conteo[sitio] = _conteo.get(sitio, 0) + 1
    n = _conteo[sitio]

    if n >= DETECCIONES_LIMITE:
        fin = time.time() + SEGUNDOS_BLOQUEO
        _bloqueados[sitio] = fin
        _bloquear_hosts(sitio)
        return (n, True, SEGUNDOS_BLOQUEO)

    return (n, False, 0)


def verificar_bloqueo(sitio: str) -> int:
    """Retorna segundos restantes de bloqueo. 0 si ya expiro."""
    fin       = _bloqueados.get(sitio, 0)
    restantes = int(fin - time.time())
    if restantes <= 0:
        if sitio in _bloqueados:
            _desbloquear_hosts(sitio)
            del _bloqueados[sitio]
        return 0
    return restantes


# ── Manejo del archivo hosts ──────────────────────────────

def _bloquear_hosts(sitio: str) -> bool:
    if not es_admin():
        log("Sin permisos Admin — bloqueo de sitio omitido", C["warn"])
        return False
    try:
        linea = "\n" + REDIRECT_IP + "\t" + sitio + "\t" + MARCA
        with open(HOSTS_PATH, "a", encoding="utf-8") as f:
            f.write(linea)
        log("Sitio bloqueado: " + sitio, C["danger"])
        os.system("ipconfig /flushdns >nul 2>&1")
        return True
    except Exception as e:
        log("Error al bloquear " + sitio + ": " + str(e), C["warn"])
        return False


def _desbloquear_hosts(sitio: str) -> bool:
    if not es_admin():
        return False
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        nuevas = [l for l in lineas if not (MARCA in l and sitio in l)]
        with open(HOSTS_PATH, "w", encoding="utf-8") as f:
            f.writelines(nuevas)
        os.system("ipconfig /flushdns >nul 2>&1")
        log("Sitio desbloqueado: " + sitio, C["safe"])
        return True
    except Exception as e:
        log("Error al desbloquear " + sitio + ": " + str(e), C["warn"])
        return False
