# -*- coding: utf-8 -*-
"""
installer.py
Auto-instalacion de dependencias al correr como .py
Se omite si el programa corre como EXE congelado (PyInstaller).
"""
import subprocess
import sys

# Forzar UTF-8 en consola Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def instalar_si_falta():
    """Instala los paquetes necesarios si no estan presentes."""
    if getattr(sys, "frozen", False):
        return  # EXE congelado — no usar pip

    paquetes = {
        "pynput":  "pynput",
        "plyer":   "plyer",
        "pystray": "pystray",
        "PIL":     "Pillow",   # PIL es el import, Pillow es el paquete pip
        "groq":    "groq",     # libreria oficial de Groq
        "python-dotenv": "python-dotenv", # para leer el .env
    }

    for modulo, paquete in paquetes.items():
        try:
            __import__(modulo)
        except ImportError:
            print("Instalando " + paquete + "...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", paquete],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print("No se pudo instalar " + paquete + ": " + str(e))
