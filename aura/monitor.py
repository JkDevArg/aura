# -*- coding: utf-8 -*-
"""
monitor.py
Captura de teclado en tiempo real con debug completo.

Flujo:
  Cada espacio/Enter → analiza buffer completo
    1. Si hay key Groq → llama Groq (unica autoridad)
    2. Si Groq falla   → localhost
    3. Si todo falla   → local de emergencia

Debug visible en el log del panel en cada paso.
"""
import threading
import time
from datetime import datetime

from pynput import keyboard

from aura.config import C, CONFIG
from aura.logger import log
from aura.detector import analizar


def _ts():
    """Timestamp corto para debug."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class MonitorTeclado:

    def __init__(self, on_alerta):
        self.on_alerta           = on_alerta
        self.buffer              = ""
        self.activo              = False
        self.bloqueado           = False
        self.analizando_ia       = False
        self.ultimo_ts_ia        = 0.0
        self.ultima_alerta       = ""
        self.listener            = None
        self.listener_bloqueador = None
        self.teclas_capturadas   = 0   # contador debug

    # ── Captura de teclas ──────────────────────────────────

    def _press(self, key):
        if not self.activo:
            return

        if key == keyboard.Key.enter and self.bloqueado:
            log("[TECLADO] Enter suprimido — alerta pendiente", C["danger"])
            return

        try:
            ch = key.char
            if ch:
                self.buffer += ch
                self.teclas_capturadas += 1
                # Log cada 5 teclas para no spamear
                if self.teclas_capturadas % 5 == 0:
                    log(
                        "[TECLADO] Buffer actual: \"" + self.buffer[-30:] + "\""
                        + " (" + str(len(self.buffer)) + " chars)",
                        C["muted"]
                    )
        except AttributeError:
            if key == keyboard.Key.space:
                self.buffer += " "
                log("[TECLADO] Espacio — analizando: \"" + self.buffer.strip()[-40:] + "\"", C["muted"])
                self._disparar_analisis()

            elif key == keyboard.Key.enter:
                log("[TECLADO] Enter — analisis forzado del buffer", C["muted"])
                self._disparar_analisis(forzar=True)
                self.buffer = ""

            elif key == keyboard.Key.backspace:
                if self.buffer:
                    self.buffer = self.buffer[:-1]

            elif key == keyboard.Key.tab:
                self.buffer += " "
                self._disparar_analisis()

    # ── Motor de analisis ──────────────────────────────────

    def _disparar_analisis(self, forzar: bool = False):
        """
        Decide si lanzar analisis segun el cooldown.
        Siempre usa el pipeline completo de detector.py
        (Groq → localhost → local segun disponibilidad).
        """
        texto = self.buffer.strip()

        # Ignorar textos muy cortos
        if len(texto) < 3:
            return

        # Ignorar si ya se alerto por este texto exacto
        if texto == self.ultima_alerta:
            log("[MONITOR] Texto ya analizado — ignorando duplicado", C["muted"])
            return

        # Cooldown para no saturar la API
        ahora       = time.time()
        cooldown_ok = (ahora - self.ultimo_ts_ia) >= CONFIG["cooldown"]

        if not cooldown_ok and not forzar:
            segs_restantes = round(CONFIG["cooldown"] - (ahora - self.ultimo_ts_ia), 1)
            log(
                "[MONITOR] Cooldown activo — " + str(segs_restantes) + "s restantes",
                C["muted"]
            )
            return

        if self.analizando_ia:
            log("[MONITOR] Ya hay un analisis en curso — esperando...", C["muted"])
            return

        # Lanzar analisis en hilo separado
        self.analizando_ia = True
        self.ultimo_ts_ia  = ahora
        log(
            "[MONITOR] Lanzando analisis para: \"" + texto[:50] + "\"",
            C["muted"]
        )
        threading.Thread(
            target=self._tarea_analisis,
            args=(texto,),
            daemon=True
        ).start()

    def _tarea_analisis(self, texto: str):
        """
        Hilo de analisis con debug completo en cada paso.
        Usa el pipeline de detector.py que maneja la prioridad
        Groq → localhost → local automaticamente.
        """
        inicio = time.time()

        try:
            # ── Debug: estado de la key ──────────────────
            key = CONFIG["groq_key"].strip()
            if key:
                log(
                    "[IA] Groq key configurada: " + key[:8] + "..." + key[-4:],
                    C["muted"]
                )
            else:
                log("[IA] Sin Groq key — usando analisis local", C["warn"])

            # ── Llamar pipeline completo ─────────────────
            log("[IA] Iniciando pipeline de deteccion...", C["muted"])
            resultado = analizar(texto)

            elapsed = round(time.time() - inicio, 2)

            # ── Debug: resultado ─────────────────────────
            if resultado is None:
                log(
                    "[IA] Resultado: SEGURO ✓  (" + str(elapsed) + "s) — \"" + texto[:40] + "\"",
                    C["safe"]
                )
                return

            nivel  = resultado.get("nivel", "?")
            score  = resultado.get("score", 0)
            fuente = resultado.get("fuente", "?")
            razon  = resultado.get("razon", "")[:70]

            log(
                "[IA] Resultado: " + nivel +
                " | score=" + str(round(score, 2)) +
                " | fuente=" + fuente +
                " (" + str(elapsed) + "s)",
                C["danger"] if nivel == "PELIGRO" else C["warn"]
            )
            log("[IA] Razon: " + razon, C["muted"])

            # ── Disparar alerta si corresponde ───────────
            if texto != self.ultima_alerta:
                self.ultima_alerta = texto
                self.buffer        = ""
                self._activar_bloqueo_enter()
                self.on_alerta(resultado, texto)
            else:
                log("[MONITOR] Alerta duplicada suprimida", C["muted"])

        except Exception as e:
            import traceback
            log("[ERROR] Excepcion en analisis: " + str(e), C["danger"])
            log("[ERROR] " + traceback.format_exc()[:200], C["danger"])

        finally:
            self.analizando_ia = False

    # ── Bloqueo de Enter ───────────────────────────────────

    def _bloquear_enter_callback(self, key):
        if key == keyboard.Key.enter:
            log("[TECLADO] Enter BLOQUEADO por alerta activa", C["danger"])
            return False

    def _activar_bloqueo_enter(self):
        self.bloqueado = True
        if self.listener_bloqueador and self.listener_bloqueador.is_alive():
            return
        self.listener_bloqueador = keyboard.Listener(
            on_press=self._bloquear_enter_callback,
            suppress=True
        )
        self.listener_bloqueador.start()
        log("[TECLADO] Enter BLOQUEADO — esperando decision del usuario", C["danger"])

    def desbloquear_enter(self):
        self.bloqueado = False
        if self.listener_bloqueador:
            self.listener_bloqueador.stop()
            self.listener_bloqueador = None
        log("[TECLADO] Enter desbloqueado", C["safe"])

    # ── Control ────────────────────────────────────────────

    def iniciar(self):
        self.activo              = True
        self.buffer              = ""
        self.bloqueado           = False
        self.ultima_alerta       = ""
        self.teclas_capturadas   = 0
        self.listener_bloqueador = None
        self.listener = keyboard.Listener(
            on_press=self._press,
            suppress=False
        )
        self.listener.start()
        log("[MONITOR] Iniciado — escuchando teclado", C["safe"])
        log(
            "[MONITOR] Key Groq: " + (
                "configurada ✓" if CONFIG["groq_key"].strip()
                else "NO configurada — solo analisis local"
            ),
            C["safe"] if CONFIG["groq_key"].strip() else C["warn"]
        )
        log(
            "[MONITOR] Cooldown entre analisis: " + str(CONFIG["cooldown"]) + "s",
            C["muted"]
        )

    def detener(self):
        self.activo = False
        if self.listener_bloqueador:
            self.listener_bloqueador.stop()
            self.listener_bloqueador = None
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.bloqueado = False
        log("[MONITOR] Detenido", C["muted"])

    def pausar(self):
        self.activo = False
        log("[MONITOR] Pausado", C["muted"])

    def reanudar(self):
        self.activo        = True
        self.buffer        = ""
        self.bloqueado     = False
        self.ultima_alerta = ""
        if self.listener_bloqueador:
            self.listener_bloqueador.stop()
            self.listener_bloqueador = None
        log("[MONITOR] Reanudado", C["safe"])
