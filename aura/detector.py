# -*- coding: utf-8 -*-
"""
aura/detector.py
Pipeline de deteccion de ciberbullying.
Prioridad: Groq → localhost → local.
"""
import json
from aura.config import C, CONFIG, OFENSIVAS
from aura.logger import log

_groq_client = None


def _get_groq_client():
    global _groq_client
    key = CONFIG["groq_key"].strip()
    if not key:
        return None
    try:
        from groq import Groq
        if _groq_client is None or getattr(_groq_client, "_aura_key", "") != key:
            _groq_client = Groq(api_key=key)
            _groq_client._aura_key = key
        return _groq_client
    except ImportError:
        log("[GROQ] Libreria no instalada: pip install groq", C["warn"])
        return None
    except Exception as e:
        log("[GROQ] Error inicializando cliente: " + str(e)[:60], C["warn"])
        return None


# ── Prompt ────────────────────────────────────────────────
_SISTEMA = (
    "Eres un sistema de deteccion de ciberbullying. "
    "Analiza el texto y determina si contiene acoso, insultos, amenazas o contenido ofensivo. "
    "Debes responder EXCLUSIVAMENTE con un objeto JSON. Nada mas. Sin markdown. Sin explicaciones fuera del JSON."
)

def _prompt(texto):
    return (
        'Texto a analizar: "' + texto + '"\n\n'
        "Clasifica el texto y responde con este JSON:\n"
        "{\n"
        '  "nivel": "<SEGURO o ADVERTENCIA o PELIGRO>",\n'
        '  "score": <numero del 0.0 al 1.0 donde 1.0 es maximo riesgo>,\n'
        '  "razon": "<explica brevemente por que es o no es ofensivo>",\n'
        '  "sugerencia": "<como podria reformularse de forma respetuosa>"\n'
        "}\n\n"
        "IMPORTANTE:\n"
        "- Usa PELIGRO si hay insultos directos, amenazas, acoso o lenguaje muy ofensivo\n"
        "- Usa ADVERTENCIA si el tono es agresivo o grosero pero no tan grave\n"
        "- Usa SEGURO SOLO si el texto es completamente inofensivo\n"
        "- El score debe reflejar el nivel de riesgo: 0.0=seguro, 1.0=muy peligroso\n"
        "- Si dices PELIGRO el score debe ser mayor a 0.6\n"
        "- Si dices SEGURO el score debe ser menor a 0.3\n"
        "Responde SOLO con el JSON, sin ningun texto adicional."
    )


# ── 1. Groq ───────────────────────────────────────────────

def detectar_groq(texto):
    client = _get_groq_client()
    if not client:
        return None

    raw = ""
    try:
        log("[GROQ] Enviando a api.groq.com: \"" + texto[:50] + "\"", C["muted"])

        completion = client.chat.completions.create(
            model=CONFIG["groq_model"],
            messages=[
                {"role": "system", "content": _SISTEMA},
                {"role": "user",   "content": _prompt(texto)},
            ],
            temperature=0.0,
            max_tokens=300,
        )

        raw   = completion.choices[0].message.content.strip()
        model = getattr(completion, "model", "llama3")
        log("[GROQ] Modelo: " + model + " | Raw: " + raw[:80], C["muted"])

        # Limpiar markdown si el modelo lo agrego de todas formas
        clean = raw.replace("```json", "").replace("```", "").strip()
        # Extraer solo el JSON si hay texto extra
        if "{" in clean:
            clean = clean[clean.index("{"):clean.rindex("}")+1]

        result = json.loads(clean)

        nivel = str(result.get("nivel", "")).upper().strip()
        score = float(result.get("score", 0.5))
        razon = str(result.get("razon", ""))

        # Sanity check: si la razon dice que es ofensivo pero nivel dice SEGURO,
        # corregir automaticamente usando el score
        if nivel == "SEGURO" and score > 0.5:
            log("[GROQ] CORRECCION: nivel=SEGURO pero score=" + str(score) +
                " — ajustando a ADVERTENCIA", C["warn"])
            nivel = "ADVERTENCIA"

        log(
            "[GROQ] Resultado: nivel=" + nivel + " score=" + str(round(score, 2)),
            C["safe"] if nivel == "SEGURO" else C["warn"] if nivel == "ADVERTENCIA" else C["danger"]
        )
        if razon:
            log("[GROQ] Razon: " + razon[:100], C["muted"])

        if nivel == "SEGURO" and score <= 0.3:
            return None   # Definitivamente seguro

        if nivel not in ("ADVERTENCIA", "PELIGRO"):
            # Nivel desconocido — inferir desde score
            nivel = "PELIGRO" if score >= 0.7 else "ADVERTENCIA" if score >= 0.4 else "SEGURO"
            if nivel == "SEGURO":
                return None

        result["nivel"]  = nivel
        result["score"]  = score
        result["fuente"] = "Groq AI (" + model + ")"
        return result

    except json.JSONDecodeError:
        log("[GROQ] JSON invalido — raw: " + raw[:120], C["danger"])
        # Intentar extraer nivel manualmente del texto
        raw_upper = raw.upper()
        if "PELIGRO" in raw_upper:
            return {"nivel": "PELIGRO", "score": 0.9, "fuente": "Groq AI",
                    "razon": "Contenido ofensivo detectado", "sugerencia": "Reformula tu mensaje"}
        if "ADVERTENCIA" in raw_upper:
            return {"nivel": "ADVERTENCIA", "score": 0.6, "fuente": "Groq AI",
                    "razon": "Tono agresivo detectado", "sugerencia": "Considera un tono mas respetuoso"}
        return None
    except Exception as e:
        import traceback
        log("[GROQ] Error: " + type(e).__name__ + " — " + str(e)[:80], C["danger"])
        log("[GROQ] " + traceback.format_exc().split("\n")[-2], C["muted"])
        return None


# ── 2. Localhost ──────────────────────────────────────────

def detectar_localhost(texto):
    import urllib.request
    endpoints = [
        ("http://localhost:11434/api/chat", "ollama"),
        ("http://localhost:1234/v1/chat/completions", "lmstudio"),
    ]
    for url, fmt in endpoints:
        try:
            if fmt == "ollama":
                payload = json.dumps({"model":"llama3","messages":[
                    {"role":"system","content":_SISTEMA},
                    {"role":"user","content":_prompt(texto)}
                ],"stream":False}).encode()
            else:
                payload = json.dumps({"model":"local-model","messages":[
                    {"role":"system","content":_SISTEMA},
                    {"role":"user","content":_prompt(texto)}
                ],"temperature":0.0,"max_tokens":300}).encode()

            req = urllib.request.Request(url, data=payload,
                                          headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                raw  = data.get("message",{}).get("content","") if fmt=="ollama" \
                       else data["choices"][0]["message"]["content"]
                clean = raw.strip().replace("```json","").replace("```","").strip()
                if "{" in clean:
                    clean = clean[clean.index("{"):clean.rindex("}")+1]
                result = json.loads(clean)
                nivel  = str(result.get("nivel","")).upper()
                score  = float(result.get("score",0.5))
                log("[LOCALHOST] " + url + " → " + nivel, C["safe"])
                if nivel == "SEGURO" and score <= 0.3:
                    return None
                result["nivel"]  = nivel if nivel in ("ADVERTENCIA","PELIGRO") else ("PELIGRO" if score>=0.7 else "ADVERTENCIA")
                result["fuente"] = "Localhost AI"
                return result
        except Exception as ex:
            log("[LOCALHOST] " + url + " no disponible: " + str(ex)[:50], C["muted"])
            continue
    return None


# ── 3. Local palabras clave ───────────────────────────────

def detectar_local(texto):
    tl = texto.lower().strip()
    encontradas = [p for p in OFENSIVAS if p in tl]
    if not encontradas:
        return None
    score = min(0.40 + len(encontradas) * 0.15, 0.99)
    nivel = "PELIGRO" if score > 0.60 else "ADVERTENCIA"
    return {
        "nivel":      nivel,
        "score":      score,
        "fuente":     "Analisis Local",
        "razon":      "Palabras detectadas: " + ", ".join(set(encontradas)),
        "sugerencia": "Intenta expresarte de forma mas respetuosa.",
    }


# ── Pipeline ──────────────────────────────────────────────

def analizar(texto):
    """
    Pipeline 100% IA:
      - Con key Groq  → solo Groq (sin fallback local)
      - Sin key       → no analiza, retorna None
      El analisis local NUNCA se usa aqui.
      detectar_local() solo se llama directamente desde monitor.py
      para el chequeo continuo mientras el usuario escribe.
    """
    texto = texto.strip()
    if not texto:
        return None

    key = CONFIG["groq_key"].strip()

    if not key:
        log("[PIPELINE] Sin Groq key — no se analiza (configura tu key en AI Shield)", C["warn"])
        return None

    log("[PIPELINE] Texto: \"" + texto[:60] + "\"", C["muted"])

    # Groq es la unica fuente de verdad
    resultado = detectar_groq(texto)

    if resultado is not None:
        return resultado

    # Groq fallo — intentar localhost como unico fallback de IA
    log("[PIPELINE] Groq no respondio — intentando localhost...", C["warn"])
    resultado = detectar_localhost(texto)

    if resultado is not None:
        return resultado

    # Sin IA disponible — NO usar local, solo informar
    log("[PIPELINE] Sin conexion a IA — analisis omitido (no se usa deteccion local)", C["warn"])
    return None
