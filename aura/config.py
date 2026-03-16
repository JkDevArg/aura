# -*- coding: utf-8 -*-
"""
config.py
Configuracion global: colores, endpoints de API y lista de palabras ofensivas.
Para agregar nuevas palabras basta editar OFENSIVAS.
Para cambiar el modelo de IA basta editar CONFIG.
"""

from dotenv import load_dotenv
load_dotenv()

# ── Configuracion de la aplicacion ────────────────────────
CONFIG = {
    "groq_key":  os.getenv("GROQ_API_KEY"),
    "groq_url":  "https://api.groq.com/openai/v1/chat/completions",
    "hf_url":    "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-offensive",
    "min_chars": 6,      # caracteres minimos antes de analizar
    "cooldown":  2.5,    # segundos entre llamadas a la IA
    "groq_model": os.getenv("MODEL_IA"),
}

# ── Paleta de colores (tema oscuro) ───────────────────────
C = {
    "bg":     "#0f0f1a",
    "card":   "#1a1a2e",
    "input":  "#16213e",
    "accent": "#7c3aed",
    "safe":   "#10b981",
    "warn":   "#f59e0b",
    "danger": "#ef4444",
    "text":   "#e2e8f0",
    "muted":  "#94a3b8",
}

# ── Palabras y frases ofensivas ───────────────────────────
# Agregar o quitar palabras aqui segun necesidad.
OFENSIVAS = [
    # Insultos directos
    "tonto", "tonta", "idiota", "estupido", "estupida",
    "imbecil", "tarado", "tarada", "inutil", "bruto", "bruta",
    "feo", "fea", "gordo", "gorda", "flaco", "flaca",
    "asco", "odio", "mierda",

    # Insultos en ingles
    "loser", "stupid", "idiot", "dumb", "ugly", "fat",

    # Slang peruano / latinoamericano
    "cojudo", "cojuda", "huevon", "huevona",
    "pendejo", "pendeja", "concha", "ctm", "animal",

    # Frases compuestas
    "eres un tonto", "eres una tonta",
    "eres un idiota", "eres una idiota",
    "eres un asco", "me das asco", "que asco",
    "te odio", "los odio",
    "te mato", "te voy a matar",
    "muerete", "ojala te", "ojala mueras",
    "nadie te quiere", "todos te odian", "eres lo peor",
    "no sirves", "no vales nada", "eres basura",
    "callate", "cierrate", "largate", "vete a",
    "perdedor", "perdedora", "fracasado", "fracasada",

    # Frases en ingles
    "kill yourself", "kys", "go die",
    "hate you", "you suck", "shut up",
    "worthless", "nobody likes you",
]
