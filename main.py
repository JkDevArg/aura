# -*- coding: utf-8 -*-
"""
main.py — Aura: Escudo Etico
"""
import sys
import os

# ── Fix de path: funciona desde cualquier directorio ─────
# Necesario especialmente cuando Windows UAC relanza el proceso
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_BASE_DIR)                    # cambiar cwd al directorio del proyecto
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

# ── Instalar dependencias si faltan ───────────────────────
try:
    from aura.installer import instalar_si_falta
    instalar_si_falta()
except Exception as e:
    print("Advertencia al instalar dependencias:", e)

# ── Lanzar la aplicacion ──────────────────────────────────
try:
    from aura.ui.dashboard import AuraDashboard
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Aura — Error de importacion",
        "No se pudo cargar un modulo necesario:\n\n" + str(e) +
        "\n\nAsegurate de que la carpeta 'aura' este junto a main.py\n"
        "y ejecuta: pip install pynput plyer pystray Pillow"
    )
    sys.exit(1)

if __name__ == "__main__":
    app = AuraDashboard()
    app.mainloop()
