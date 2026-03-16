# -*- coding: utf-8 -*-
"""
ui/panel.py
Panel de control principal de Aura: Escudo Etico.
Muestra estado, estadisticas, log en tiempo real y configuracion de API.
Se minimiza a la bandeja del sistema al cerrar.
"""
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from pynput.keyboard import Controller as KbController, Key

from aura.config import C, CONFIG
from aura.logger import log, registrar_callback
from aura.monitor import MonitorTeclado
from aura.detector import detectar_groq
from aura.site_blocker import sitio_activo, registrar_deteccion, verificar_bloqueo
from aura.ui.alerta_popup import AlertaPopup

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_OK = True
except Exception:
    TRAY_OK = False

try:
    from plyer import notification as plyer_notif
    PLYER_OK = True
except Exception:
    PLYER_OK = False


class PanelControl:
    """Ventana principal de Aura: Escudo Etico."""

    def __init__(self):
        self.root      = tk.Tk()
        self.root.title("Aura: Escudo Etico - Panel de Control")
        self.root.geometry("540x700")
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)

        self.monitor   = MonitorTeclado(on_alerta=self._alerta_recibida)
        self.encendido = False
        self.n_alertas = 0
        self.tray_icon = None

        # Conectar logger global a este panel
        registrar_callback(self._log)

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

    # ── Construccion de la UI ─────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["accent"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Aura: Escudo Etico",
                 font=("Segoe UI", 18, "bold"),
                 fg="white", bg=C["accent"]).pack()
        tk.Label(hdr,
                 text="Innovacion Tecnologica contra el Acoso Digital",
                 font=("Segoe UI", 8),
                 fg="#ddd6fe", bg=C["accent"]).pack()

        main = tk.Frame(self.root, bg=C["bg"], padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Tarjeta de estado
        ec = tk.Frame(main, bg=C["card"], padx=16, pady=14)
        ec.pack(fill="x", pady=(0, 10))
        top = tk.Frame(ec, bg=C["card"])
        top.pack(fill="x")

        self.ico_lbl = tk.Label(top, text="||",
                                 font=("Segoe UI", 22, "bold"),
                                 bg=C["card"], fg=C["muted"])
        self.ico_lbl.pack(side="left")

        info = tk.Frame(top, bg=C["card"])
        info.pack(side="left", padx=12)
        self.est_lbl = tk.Label(info, text="Monitor detenido",
                                 font=("Segoe UI", 14, "bold"),
                                 fg=C["muted"], bg=C["card"])
        self.est_lbl.pack(anchor="w")
        self.est_sub = tk.Label(info, text="Presiona Activar para protegerte",
                                 font=("Segoe UI", 9),
                                 fg=C["muted"], bg=C["card"])
        self.est_sub.pack(anchor="w")

        # Boton ON/OFF
        self.btn = tk.Button(main,
                              text="ACTIVAR PROTECCION",
                              font=("Segoe UI", 13, "bold"),
                              bg=C["safe"], fg="white",
                              activebackground="#059669",
                              relief="flat", bd=0, pady=14,
                              cursor="hand2",
                              command=self._toggle)
        self.btn.pack(fill="x", pady=(0, 10))

        # Stats
        sf = tk.Frame(main, bg=C["bg"])
        sf.pack(fill="x", pady=(0, 10))
        sf.columnconfigure((0, 1, 2), weight=1)
        self.stat_alertas   = self._stat(sf, "0",   "Alertas hoy",  C["danger"], 0)
        self.stat_revisados = self._stat(sf, "0",   "Analizados",   C["warn"],   1)
        self.stat_estado    = self._stat(sf, "OFF", "Estado",       C["muted"],  2)

        # API Key
        af = tk.LabelFrame(main,
                            text="  API Key de Groq (gratis en console.groq.com)  ",
                            bg=C["card"], fg=C["muted"],
                            font=("Segoe UI", 8), relief="flat",
                            padx=10, pady=8)
        af.pack(fill="x", pady=(0, 10))

        self.key_entry = tk.Entry(af, show="*",
                                   bg=C["input"], fg=C["text"],
                                   insertbackground=C["text"],
                                   font=("Segoe UI", 9),
                                   relief="flat", bd=4)
        self.key_entry.pack(fill="x", pady=(0, 6))

        br = tk.Frame(af, bg=C["card"])
        br.pack(fill="x")
        tk.Button(br, text="Guardar key y probar conexion",
                  font=("Segoe UI", 8),
                  bg=C["accent"], fg="white",
                  relief="flat", bd=0, padx=10, pady=4,
                  cursor="hand2",
                  command=self._guardar_key).pack(side="left")
        self.key_status = tk.Label(br, text="Sin key — modo local activo",
                                    font=("Segoe UI", 8),
                                    fg=C["muted"], bg=C["card"])
        self.key_status.pack(side="right")

        # Log en tiempo real
        lf = tk.LabelFrame(main, text="  Log en tiempo real  ",
                            bg=C["card"], fg=C["muted"],
                            font=("Segoe UI", 8), relief="flat",
                            padx=10, pady=8)
        lf.pack(fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            lf, height=12, wrap="word",
            bg=C["input"], fg=C["text"],
            font=("Consolas", 8), relief="flat", bd=0,
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_configure("warn",   foreground=C["warn"])
        self.log_text.tag_configure("danger", foreground=C["danger"])
        self.log_text.tag_configure("safe",   foreground=C["safe"])
        self.log_text.tag_configure("muted",  foreground=C["muted"])

        # Barra de estado
        sb = tk.Frame(self.root, bg=C["card"], pady=4)
        sb.pack(fill="x", side="bottom")
        self.status = tk.Label(sb, text="Inactivo",
                                font=("Segoe UI", 8),
                                fg=C["muted"], bg=C["card"])
        self.status.pack(side="left", padx=10)

    def _stat(self, parent, valor, label, color, col):
        card = tk.Frame(parent, bg=C["card"], padx=10, pady=8)
        card.grid(row=0, column=col, padx=3, sticky="ew")
        lv = tk.Label(card, text=valor,
                      font=("Segoe UI", 22, "bold"),
                      fg=color, bg=C["card"])
        lv.pack()
        tk.Label(card, text=label,
                 font=("Segoe UI", 8),
                 fg=C["muted"], bg=C["card"]).pack()
        return lv

    # ── Logica del monitor ────────────────────────────────

    def _toggle(self):
        if not self.encendido:
            self._activar()
        else:
            self._desactivar()

    def _activar(self):
        self.encendido = True
        self.monitor.iniciar()
        self.ico_lbl.configure(text="ON",  fg=C["safe"])
        self.est_lbl.configure(text="Proteccion ACTIVA", fg=C["safe"])
        self.est_sub.configure(
            text="Monitoreando lo que escribes en cualquier app...",
            fg=C["safe"]
        )
        self.btn.configure(text="PAUSAR PROTECCION", bg=C["danger"])
        self.stat_estado.configure(text="ON", fg=C["safe"])
        self.status.configure(text="Monitoreando teclado", fg=C["safe"])
        self._log("Monitor activado", C["safe"])
        self._notif("Aura: Escudo Etico Activo", "Monitoreando mientras escribes.")

    def _desactivar(self):
        self.encendido = False
        self.monitor.detener()
        self.ico_lbl.configure(text="||",  fg=C["muted"])
        self.est_lbl.configure(text="Monitor pausado",    fg=C["muted"])
        self.est_sub.configure(text="Presiona Activar para reanudar", fg=C["muted"])
        self.btn.configure(text="ACTIVAR PROTECCION", bg=C["safe"])
        self.stat_estado.configure(text="OFF", fg=C["muted"])
        self.status.configure(text="Inactivo", fg=C["muted"])
        self._log("Monitor pausado", C["muted"])

    # ── API Key ───────────────────────────────────────────

    def _guardar_key(self):
        key = self.key_entry.get().strip()
        CONFIG["groq_key"] = key
        if key:
            self.key_status.configure(text="Probando conexion...", fg=C["warn"])
            self._log("Probando Groq API...", C["warn"])
            threading.Thread(target=self._probar_groq, daemon=True).start()
        else:
            CONFIG["groq_key"] = ""
            self.key_status.configure(text="Sin key — modo local activo", fg=C["muted"])
            self._log("Key borrada — usando analisis local", C["muted"])

    def _probar_groq(self):
        detectar_groq("hola")   # llamada de prueba
        def upd():
            if CONFIG["groq_key"]:
                self.key_status.configure(text="Groq conectado", fg=C["safe"])
                self._log("Groq API conectada correctamente", C["safe"])
        self.root.after(0, upd)

    # ── Alertas ───────────────────────────────────────────

    def _alerta_recibida(self, resultado, texto):
        """Llamado desde hilo secundario — delegar al hilo principal."""
        self.root.after(0, self._mostrar_alerta, resultado, texto)

    def _mostrar_alerta(self, resultado, texto):
        self.n_alertas += 1
        self.stat_alertas.configure(text=str(self.n_alertas))
        self.stat_revisados.configure(text=str(self.n_alertas))

        nivel = resultado.get("nivel", "ADVERTENCIA")
        color = C["danger"] if nivel == "PELIGRO" else C["warn"]
        self._log('ALERTA ' + nivel + ': "' + texto[:60] + '"', color)

        # Registrar en el site blocker
        sitio = sitio_activo()
        if sitio:
            n, bloqueado, segs = registrar_deteccion(sitio)
            self._log("Deteccion #" + str(n) + " en " + sitio, C["warn"])
            if bloqueado:
                self._log(sitio + " BLOQUEADO por 3 minutos", C["danger"])
                self._notif("Sitio bloqueado: " + sitio,
                            "3 detecciones — acceso bloqueado 3 min.")
                self._programar_desbloqueo(sitio, segs)

        self._notif("Aura — " + nivel,
                    resultado.get("razon", "Posible ciberbullying.")[:80])

        self.monitor.pausar()

        def on_decision(decision):
            self.monitor.desbloquear_enter()
            if decision == "continuar":
                self._log("Usuario envio de todas formas", C["warn"])
                kb = KbController()
                kb.press(Key.enter)
                kb.release(Key.enter)
            else:
                self._log("Usuario eligio editar", C["safe"])
            self.monitor.reanudar()

        popup = AlertaPopup(self.root, resultado, texto, on_decision=on_decision)
        self.root.wait_window(popup.win)

    def _programar_desbloqueo(self, sitio, segs):
        def _check():
            restantes = verificar_bloqueo(sitio)
            if restantes > 0:
                self.root.after(15_000, _check)
            else:
                self._log("Sitio " + sitio + " desbloqueado", C["safe"])
                self._notif("Desbloqueado: " + sitio, "Ya puedes acceder.")
        self.root.after(segs * 1000, _check)

    # ── Log ───────────────────────────────────────────────

    def _log(self, msg: str, color: str = None):
        color = color or C["muted"]
        hora  = datetime.now().strftime("%H:%M:%S")
        linea = "[" + hora + "] " + msg + "\n"
        tag   = {
            C["warn"]:   "warn",
            C["danger"]: "danger",
            C["safe"]:   "safe",
        }.get(color, "muted")

        def _ins():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", linea, tag)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.root.after(0, _ins)

    # ── Notificaciones ────────────────────────────────────

    def _notif(self, titulo: str, mensaje: str):
        if PLYER_OK:
            try:
                plyer_notif.notify(
                    title=titulo, message=mensaje,
                    app_name="Aura: Escudo Etico", timeout=4
                )
            except Exception:
                pass

    # ── Bandeja del sistema ───────────────────────────────

    def _crear_icono_tray(self):
        if not TRAY_OK:
            return None
        size = 64
        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d    = ImageDraw.Draw(img)
        d.ellipse([2, 2, size - 2, size - 2], fill=(124, 58, 237, 255))
        cx, cy = size // 2, size // 2
        pts = [cx, 10, cx+20, 20, cx+20, 38, cx, 54, cx-20, 38, cx-20, 20]
        d.polygon(pts, fill=(255, 255, 255, 230))
        return img

    def _iniciar_tray(self):
        if not TRAY_OK:
            return
        icono = self._crear_icono_tray()
        if not icono:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Abrir Aura", self._mostrar_ventana, default=True),
            pystray.MenuItem("Activar",    lambda: self.root.after(0, self._activar)),
            pystray.MenuItem("Pausar",     lambda: self.root.after(0, self._desactivar)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir",      lambda: self.root.after(0, self._salir_total)),
        )

        self.tray_icon = pystray.Icon(
            "AuraEscudoEtico", icono,
            "Aura: Escudo Etico — Proteccion Activa",
            menu
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _mostrar_ventana(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    # ── Ciclo de vida ─────────────────────────────────────

    def _cerrar(self):
        """Minimizar a bandeja en vez de cerrar."""
        self.root.withdraw()

    def _salir_total(self):
        self.monitor.detener()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)
        self._iniciar_tray()
        self.root.mainloop()
