# -*- coding: utf-8 -*-
"""
logger.py
Sistema de log global compartido entre todos los modulos.
El PanelControl registra su callback aqui al iniciarse.
"""
from aura.config import C

_callback = None   # funcion (msg: str, color: str) -> None


def registrar_callback(fn):
    """El PanelControl llama esto para recibir los mensajes del log."""
    global _callback
    _callback = fn


def log(msg: str, color: str = None):
    """Envia un mensaje al log. Si no hay callback, lo ignora silenciosamente."""
    if _callback:
        _callback(msg, color or C["muted"])
