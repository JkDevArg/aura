# -*- coding: utf-8 -*-
"""
ui/alerta_popup.py
Ventana de alerta modal que bloquea toda la pantalla.

Cuando se detecta ciberbullying:
  - Overlay negro semitransparente cubre toda la pantalla
  - Popup centrado encima con el detalle de la deteccion
  - grab_set_global() impide interactuar con cualquier otra ventana
  - Windows API fuerza el foco al popup

El usuario debe elegir "Editar" o "Enviar de todas formas".
"""
import ctypes
import tkinter as tk

from aura.config import C


class AlertaPopup:
    """
    Popup modal de alerta con overlay de pantalla completa.

    Parametros:
        parent      : ventana padre (root de tkinter)
        resultado   : dict con nivel, score, razon, sugerencia, fuente
        texto       : texto ofensivo detectado
        on_decision : callback(decision: str) donde decision es 'editar' o 'continuar'
    """

    def __init__(self, parent, resultado: dict, texto: str, on_decision=None):
        self.on_decision = on_decision
        self.decision    = "editar"   # default seguro si cierran sin elegir
        self.overlay     = None

        # ── Crear ventana ──────────────────────────────────
        self.win = tk.Toplevel(parent)
        self.win.title("Aura: Escudo Etico — Alerta")
        self.win.configure(bg=C["card"])
        self.win.resizable(False, False)

        # ── Bloqueo total de pantalla ──────────────────────
        self.win.attributes("-topmost", True)       # siempre encima
        self.win.grab_set_global()                  # bloquea toda la UI del SO
        self.win.focus_force()                      # foco inmediato
        self.win.protocol("WM_DELETE_WINDOW", self._editar)  # X = editar
        self.win.after(50, self._forzar_frente)     # Win API al frente

        # ── Extraer datos del resultado ────────────────────
        nivel  = resultado.get("nivel",  "ADVERTENCIA")
        score  = float(resultado.get("score", 0.5))
        razon  = resultado.get("razon",  "")
        sug    = resultado.get("sugerencia", "")
        fuente = resultado.get("fuente", "local")

        color     = C["danger"] if nivel == "PELIGRO" else C["warn"]
        title_txt = "Ciberbullying detectado" if nivel == "PELIGRO" else "Revisa tu mensaje"

        # ── Header ────────────────────────────────────────
        hdr = tk.Frame(self.win, bg=color, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title_txt,
                 font=("Segoe UI", 14, "bold"),
                 fg="white", bg=color).pack(anchor="w")
        tk.Label(hdr,
                 text="Enter bloqueado — elige una opcion para continuar",
                 font=("Segoe UI", 9, "bold"),
                 fg="white", bg=color).pack(anchor="w", pady=(4, 0))

        # ── Cuerpo ────────────────────────────────────────
        body = tk.Frame(self.win, bg=C["card"], padx=20, pady=14)
        body.pack(fill="both", expand=True)

        # Texto detectado
        tk.Label(body, text="Texto detectado:",
                 font=("Segoe UI", 9, "bold"),
                 fg=C["muted"], bg=C["card"]).pack(anchor="w")
        caja = tk.Text(body, height=3, wrap="word",
                       bg=C["input"], fg=C["text"],
                       font=("Segoe UI", 10), relief="flat", bd=4)
        caja.pack(fill="x", pady=(2, 10))
        caja.insert("1.0", texto[:300])
        caja.configure(state="disabled")

        # Barra de riesgo
        tk.Label(body,
                 text="Nivel de riesgo: " + str(int(score * 100)) + "%  |  " + fuente,
                 font=("Segoe UI", 9, "bold"),
                 fg=color, bg=C["card"]).pack(anchor="w")
        canvas = tk.Canvas(body, height=10, bg=C["input"], highlightthickness=0)
        canvas.pack(fill="x", pady=(2, 10))
        canvas.update()
        w = canvas.winfo_width() or 440
        canvas.create_rectangle(0, 0, int(w * score), 10, fill=color, outline="")

        # Razon
        if razon:
            tk.Label(body, text=razon,
                     font=("Segoe UI", 9), fg=C["text"], bg=C["card"],
                     wraplength=420, justify="left").pack(anchor="w", pady=(0, 6))

        # Sugerencia
        if sug:
            sf = tk.Frame(body, bg="#1e3a2f", padx=10, pady=8)
            sf.pack(fill="x", pady=(0, 10))
            tk.Label(sf, text="Sugerencia: " + sug,
                     font=("Segoe UI", 9), fg="#6ee7b7", bg="#1e3a2f",
                     wraplength=400, justify="left").pack(anchor="w")

        # Botones
        bf = tk.Frame(body, bg=C["card"])
        bf.pack(fill="x", pady=(10, 0))

        tk.Button(bf, text="Editar mi mensaje",
                  font=("Segoe UI", 10, "bold"),
                  bg=color, fg="white",
                  relief="flat", bd=0, padx=16, pady=10,
                  cursor="hand2",
                  command=self._editar).pack(side="left", padx=(0, 8))

        tk.Button(bf, text="Enviar de todas formas",
                  font=("Segoe UI", 9),
                  bg=C["input"], fg=C["muted"],
                  relief="flat", bd=0, padx=12, pady=10,
                  cursor="hand2",
                  command=self._continuar).pack(side="left")

        self._centrar()
        self._crear_overlay(parent)

    # ── Overlay ───────────────────────────────────────────

    def _crear_overlay(self, parent):
        """Ventana negra semitransparente que cubre toda la pantalla."""
        try:
            self.overlay = tk.Toplevel(parent)
            sw = self.overlay.winfo_screenwidth()
            sh = self.overlay.winfo_screenheight()
            self.overlay.geometry(str(sw) + "x" + str(sh) + "+0+0")
            self.overlay.configure(bg="black")
            self.overlay.attributes("-alpha", 0.55)
            self.overlay.attributes("-topmost", True)
            self.overlay.overrideredirect(True)   # sin bordes ni barra de titulo
            self.overlay.lower(self.win)          # detras del popup
            self.overlay.bind("<Button-1>", lambda e: self._forzar_frente())
        except Exception:
            self.overlay = None

    def _destruir_overlay(self):
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
        except Exception:
            pass

    # ── Foco ──────────────────────────────────────────────

    def _forzar_frente(self):
        """Usa Windows API para garantizar que el popup este al frente."""
        try:
            win_hwnd = int(self.win.wm_frame(), 16)
            ctypes.windll.user32.SetForegroundWindow(win_hwnd)
            ctypes.windll.user32.BringWindowToTop(win_hwnd)
            ctypes.windll.user32.SetActiveWindow(win_hwnd)
        except Exception:
            pass
        self.win.focus_force()
        self.win.lift()

    # ── Acciones ──────────────────────────────────────────

    def _editar(self):
        self.decision = "editar"
        self._destruir_overlay()
        if self.on_decision:
            self.on_decision("editar")
        self.win.destroy()

    def _continuar(self):
        self.decision = "continuar"
        self._destruir_overlay()
        if self.on_decision:
            self.on_decision("continuar")
        self.win.destroy()

    # ── Posicion ──────────────────────────────────────────

    def _centrar(self):
        self.win.update_idletasks()
        w  = 480
        h  = self.win.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(
            str(w) + "x" + str(h) +
            "+" + str((sw - w) // 2) +
            "+" + str((sh - h) // 2)
        )
