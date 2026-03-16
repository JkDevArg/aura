# -*- coding: utf-8 -*-
"""aura/scoring.py — Sistema de puntuacion dinamica con Groq."""
from aura.config import CONFIG, C
from aura.logger import log

PUNTOS = {"LEVE": 5, "MODERADO": 15, "CRITICO": 30}
UMBRAL_ALERTA = 50


def evaluar_severidad_groq(texto, resultado_ia):
    key = CONFIG["groq_key"].strip()
    if key:
        try:
            from groq import Groq
            client = Groq(api_key=key)
            prompt = (
                "Clasifica la SEVERIDAD de este ciberbullying para un sistema de reputacion.\n\n"
                "Texto: \"" + texto[:200] + "\"\n"
                "Nivel detectado: " + resultado_ia.get("nivel","ADVERTENCIA") + "\n"
                "Score de riesgo: " + str(resultado_ia.get("score",0.5)) + "\n"
                "Razon: " + resultado_ia.get("razon","") + "\n\n"
                "Responde SOLO con uno de estos valores exactos (sin mas texto):\n"
                "LEVE\nMODERADO\nCRITICO\n\n"
                "- LEVE: tono agresivo, insulto menor\n"
                "- MODERADO: bullying claro, ofensa directa, humillacion\n"
                "- CRITICO: amenaza, acoso grave, incitacion al odio"
            )
            completion = client.chat.completions.create(
                model=CONFIG["groq_model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0, max_tokens=20,
            )
            resp = completion.choices[0].message.content.strip().upper()
            if resp in ("LEVE", "MODERADO", "CRITICO"):
                log("[SCORING] Groq -> severidad: " + resp + " (-" + str(PUNTOS[resp]) + " pts)", C["warn"])
                return resp
        except Exception as e:
            log("[SCORING] Groq error: " + str(e)[:60], C["warn"])

    # Fallback sin Groq
    score = resultado_ia.get("score", 0.5)
    nivel = resultado_ia.get("nivel", "ADVERTENCIA")
    if nivel == "PELIGRO" and score >= 0.85:
        sev = "CRITICO"
    elif nivel == "PELIGRO" or score >= 0.65:
        sev = "MODERADO"
    else:
        sev = "LEVE"
    log("[SCORING] Severidad inferida (sin Groq): " + sev, C["muted"])
    return sev


def procesar_deteccion(texto, resultado_ia, sitio=""):
    from aura.database import bajar_score, registrar_deteccion
    severidad = evaluar_severidad_groq(texto, resultado_ia)
    puntos    = PUNTOS.get(severidad, 5)
    det_id    = registrar_deteccion(
        texto=texto, nivel=severidad,
        score_ia=float(resultado_ia.get("score", 0.5)),
        fuente=resultado_ia.get("fuente", "?"),
        razon=resultado_ia.get("razon", ""),
        sugerencia=resultado_ia.get("sugerencia", ""),
        sitio=sitio, puntos_rest=puntos,
    )
    score_nuevo = bajar_score(puntos)
    log("[SCORING] Score: " + str(score_nuevo) + " (-" + str(puntos) + " por " + severidad + ")",
        C["danger"] if score_nuevo <= UMBRAL_ALERTA else C["warn"])
    return {
        "deteccion_id": det_id, "severidad": severidad,
        "puntos": puntos, "score_nuevo": score_nuevo,
        "alerta_score_bajo": score_nuevo <= UMBRAL_ALERTA,
    }


def get_consecuencias(score):
    if score <= 0:
        return ["Acceso bloqueado a todas las redes sociales",
                "Notificacion enviada al administrador",
                "Sesion de concientizacion obligatoria requerida"]
    if score <= 20:
        return ["Bloqueo temporal de 24h en redes sociales",
                "Reporte automatico generado",
                "Restriccion de envio de mensajes activa"]
    if score <= 35:
        return ["Bloqueo de sitios por 3 horas",
                "Alerta enviada al panel de supervision",
                "Proxima infraccion: bloqueo extendido"]
    return ["Tu reputacion digital esta en riesgo",
            "Proxima infraccion: sitios bloqueados 1 hora",
            "Revisa las guias de conducta digital"]
