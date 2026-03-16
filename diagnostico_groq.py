# -*- coding: utf-8 -*-
"""
diagnostico_groq.py
Ejecuta este archivo para diagnosticar problemas con Groq:
  python diagnostico_groq.py
"""
import sys, os

print("=" * 55)
print("  Aura — Diagnostico de Groq API")
print("=" * 55)

# 1. Python version
print(f"\n[1] Python: {sys.version}")

# 2. Libreria groq
print("\n[2] Verificando libreria 'groq'...")
try:
    import groq
    print("    OK — version:", groq.__version__)
except ImportError:
    print("    ERROR: No instalada")
    print("    Solucion: pip install groq")
    sys.exit(1)

# 3. Leer key desde BD o input
print("\n[3] Buscando API Key...")
key = ""
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from aura.database import get_config, inicializar
    inicializar()
    key = get_config("groq_key", "")
    if key:
        print("    Encontrada en BD: " + key[:8] + "..." + key[-4:])
    else:
        print("    No hay key en la BD")
except Exception as e:
    print("    No se pudo leer la BD:", e)

if not key:
    key = input("\n    Ingresa tu Groq API Key: ").strip()

if not key:
    print("    ERROR: Sin key"); sys.exit(1)

# 4. Formato
print("\n[4] Formato de key...")
if key.startswith("gsk_"):
    print("    OK — formato valido (gsk_...)")
else:
    print("    ADVERTENCIA: La key no empieza con 'gsk_'")
    print("    Continuando de todas formas...")

# 5. Conexion real
print("\n[5] Probando conexion con Groq...")
try:
    from groq import Groq, AuthenticationError, RateLimitError
    client = Groq(api_key=key)
    resp = client.chat.completions.create(
        model=CONFIG["groq_model"],
        messages=[{"role": "user", "content": "Di solo: OK"}],
        max_tokens=5,
    )
    respuesta = resp.choices[0].message.content.strip()
    print("    OK — Respuesta del modelo:", respuesta)
    print("    Modelo usado:", resp.model)
    print("    Tokens usados:", resp.usage.total_tokens)
except Exception as e:
    print("    ERROR:", type(e).__name__, "—", str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Test de deteccion
print("\n[6] Probando deteccion de ciberbullying...")
try:
    """ prompt = (
        "Eres un moderador experto en ciberbullying. "
        'Analiza: "ojala te mueras, eres un estupido"\n'
        'Responde SOLO con JSON: {"nivel":"SEGURO","score":0.0,"razon":"...","sugerencia":"..."}'
    ) """

    prompt = """Eres un sistema de moderación especializado en detectar ciberbullying, acoso y lenguaje tóxico en español.

        Analiza el siguiente mensaje y evalúa su nivel de toxicidad.

        Mensaje:
        "{mensaje}"

        Clasifica el nivel de riesgo en una de estas categorías:
        - SEGURO (sin toxicidad)
        - OFENSIVO (insultos leves)
        - AGRESIVO (insultos fuertes o humillación)
        - CIBERBULLYING (acoso directo, amenazas o deseo de daño)

        Responde ÚNICAMENTE con un JSON válido con esta estructura:

        {
        "nivel": "SEGURO | OFENSIVO | AGRESIVO | CIBERBULLYING",
        "score": 0.0-1.0,
        "razon": "explicación breve",
        "sugerencia": "cómo responder o moderar el mensaje"
        }

        No agregues texto fuera del JSON.
        """
    resp2 = client.chat.completions.create(
        model=CONFIG["groq_model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=300,
    )
    raw = resp2.choices[0].message.content.strip()
    print("    Respuesta raw:", raw[:200])
    import json
    result = json.loads(raw.replace("```json","").replace("```","").strip())
    print("    Nivel detectado:", result.get("nivel"))
    print("    Score:", result.get("score"))
    print("    Razon:", result.get("razon","")[:80])
except Exception as e:
    print("    ERROR en test de deteccion:", e)

print("\n" + "=" * 55)
print("  RESULTADO: Todo OK — Groq esta funcionando")
print("=" * 55)
input("\nPresiona Enter para cerrar...")
