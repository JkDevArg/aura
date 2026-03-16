# 🛡️ Aura: Escudo Ético
### Sistema de Prevención de Ciberbullying en Tiempo Real

> **Hackathon 8M · IEEE RAMA UNI / WIE UPC / WIE UNI / WIE UNMSM**  
> *Innovación Tecnológica contra el Acoso Digital con Inteligencia Artificial*

---

## Índice

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura](#arquitectura)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Instalación y Ejecución](#instalación-y-ejecución)
5. [Configuración](#configuración)
6. [Módulos del Sistema](#módulos-del-sistema)
7. [Base de Datos](#base-de-datos)
8. [Sistema de Puntuación](#sistema-de-puntuación)
9. [Pipeline de Detección IA](#pipeline-de-detección-ia)
10. [Interfaz de Usuario](#interfaz-de-usuario)
11. [Panel de Debug](#panel-de-debug)
12. [Bloqueo de Sitios Web](#bloqueo-de-sitios-web)
13. [Generar EXE](#generar-exe)
14. [Guía de Contribución](#guía-de-contribución)

---

## Descripción del Proyecto

**Aura: Escudo Ético** es una aplicación de escritorio para Windows que actúa como un **guardián ético en tiempo real**. Funciona como un antivirus pero para el lenguaje: captura lo que el usuario escribe en cualquier aplicación (redes sociales, WhatsApp, Discord, navegadores) y analiza el contenido con Inteligencia Artificial antes de que se envíe.

### Problema que resuelve

El ciberbullying ocurre cuando ya es demasiado tarde. Aura interviene **antes** del envío, no después.

### Características principales

| Característica | Descripción |
|---|---|
| 🔍 Detección en tiempo real | Analiza cada palabra mientras se escribe |
| 🤖 IA Groq (LLaMA3) | Comprensión de contexto y lenguaje natural |
| 🔒 Bloqueo de Enter | Impide enviar hasta que el usuario decida |
| 📊 Reputation Score | Puntuación dinámica de ciudadanía digital (0-100) |
| 🌐 Bloqueo de sitios | Bloquea acceso a redes sociales tras reincidencia |
| 💾 Base de datos local | Historial completo en SQLite |
| 🐛 Panel de debug | Herramienta de diagnóstico integrada |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    AURA: ESCUDO ÉTICO                   │
├──────────────┬──────────────────┬───────────────────────┤
│  CAPTURA     │   ANÁLISIS IA    │    RESPUESTA          │
│              │                  │                       │
│  pynput      │  Groq API        │  Popup Espejo         │
│  (teclado)   │  (LLaMA3)        │  de Empatía           │
│     ↓        │      ↓           │       ↓               │
│  buffer      │  localhost       │  Prompt Restricted    │
│  de texto    │  (Ollama/LMStudio│       ↓               │
│              │                  │  Score dinámico       │
│              │  [sin IA: None]  │       ↓               │
│              │                  │  Bloqueo sitios       │
└──────────────┴──────────────────┴───────────────────────┘
                        ↓
              ┌─────────────────┐
              │  SQLite DB      │
              │  aura_data.db   │
              └─────────────────┘
```

### Flujo completo de una detección

```
Usuario escribe "eres un idiota" en Facebook
        ↓
MonitorTeclado captura tecla por tecla
        ↓
Al presionar espacio → _disparar_analisis()
        ↓
detector.analizar(texto)
        ↓
    ¿Hay Groq key?
    ├── SÍ → detectar_groq()
    │         ├── Groq responde → resultado definitivo
    │         └── Groq falla   → detectar_localhost()
    │                             └── Falla → None (sin alerta)
    └── NO → None (sin alerta)
        ↓
resultado != None → on_alerta()
        ↓
scoring.procesar_deteccion()
    ├── Groq evalúa severidad: LEVE / MODERADO / CRITICO
    └── Baja score: -5 / -15 / -30 pts
        ↓
Popup según severidad:
    LEVE/MODERADO → EspejoEmpatia (reflexión + countdown)
    CRITICO       → PromptRestricted (bloqueo ético)
        ↓
Enter bloqueado hasta que usuario elija
        ↓
Score ≤ 50 → AlertaScoreCritico (consecuencias)
        ↓
Todo guardado en SQLite
```

---

## Estructura de Archivos

```
proyecto/
├── main.py                    ← Punto de entrada
├── build_exe.bat              ← Genera el EXE con PyInstaller
├── diagnostico_groq.py        ← Herramienta de diagnóstico
├── aura_data.db               ← Base de datos (se crea automáticamente)
│
└── aura/
    ├── __init__.py
    ├── config.py              ← Configuración global, colores, palabras
    ├── database.py            ← Capa de acceso a SQLite
    ├── detector.py            ← Pipeline de detección IA
    ├── installer.py           ← Auto-instalación de dependencias
    ├── logger.py              ← Sistema de log global
    ├── monitor.py             ← Captura de teclado (pynput)
    ├── scoring.py             ← Sistema de puntuación de reputación
    ├── site_blocker.py        ← Bloqueo de sitios via archivo hosts
    │
    └── ui/
        ├── __init__.py
        ├── dashboard.py       ← Dashboard completo (vista principal)
        ├── panel.py           ← Panel de control alternativo
        └── alerta_popup.py    ← Popup de alerta (versión simple)
```

---

## Instalación y Ejecución

### Requisitos

- **Windows 10/11** (64-bit)
- **Python 3.10+**
- Conexión a internet (para Groq API)

### Pasos

```bash
# 1. Clonar o descargar el proyecto
cd aura

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install pynput plyer pystray Pillow groq

# 4. Ejecutar
python main.py
```

> **⚠️ Importante:** Ejecutar como **Administrador** para que el monitor de teclado funcione en navegadores (Chrome, Firefox, Brave) y para el bloqueo de sitios.

### Dependencias

| Paquete | Versión mínima | Uso |
|---|---|---|
| `pynput` | 1.7+ | Captura de teclado global |
| `groq` | 0.9+ | Cliente oficial de Groq API |
| `plyer` | 2.1+ | Notificaciones del sistema |
| `pystray` | 0.19+ | Ícono en bandeja del sistema |
| `Pillow` | 10.0+ | Generación del ícono de bandeja |

---

## Configuración

### Groq API Key

1. Crear cuenta gratuita en [console.groq.com](https://console.groq.com)
2. Generar una API Key (empieza con `gsk_`)
3. En la app: ir a **AI Shield** → pegar la key → **Guardar y Probar**

La key se guarda automáticamente en la base de datos y persiste entre sesiones.

### Diagnóstico de conexión

Si hay problemas con Groq, ejecutar:

```bash
python diagnostico_groq.py
```

Esto verifica paso a paso: librería instalada, formato de key, conexión, y prueba de detección.

### Parámetros en `config.py`

```python
CONFIG = {
    "groq_key":  "",     # API key (se sobreescribe desde la BD)
    "min_chars": 6,      # Mínimo de caracteres para analizar
    "cooldown":  2.5,    # Segundos entre llamadas a la IA
}
```

### Agregar palabras al diccionario local

Editar la lista `OFENSIVAS` en `aura/config.py`:

```python
OFENSIVAS = [
    "tu_nueva_palabra",
    "otra frase ofensiva",
    # ... el resto
]
```

> Nota: El diccionario local (`OFENSIVAS`) solo se usa como referencia interna. El pipeline principal usa exclusivamente Groq para las detecciones.

---

## Módulos del Sistema

### `main.py`
Punto de entrada. Agrega el directorio al `sys.path`, instala dependencias si faltan, y lanza `AuraDashboard`.

### `aura/config.py`
Configuración centralizada: colores del tema, parámetros de la API, y lista de palabras ofensivas de referencia.

### `aura/logger.py`
Sistema de log global con callback. El `PanelControl` registra su función de log aquí al iniciarse, y todos los módulos la usan con `log(mensaje, color)`.

### `aura/installer.py`
Auto-instalación de paquetes via `pip` al inicio. Se omite si el programa corre como EXE congelado (`sys.frozen`).

### `aura/monitor.py`
Captura global de teclado usando `pynput`. Funciona en segundo plano monitoreando todo lo que el usuario escribe.

**Métodos públicos:**

| Método | Descripción |
|---|---|
| `iniciar()` | Inicia la escucha del teclado |
| `detener()` | Detiene completamente el monitor |
| `pausar()` | Pausa temporalmente (durante el popup) |
| `reanudar()` | Reanuda tras cerrar el popup |
| `desbloquear_enter()` | Libera el Enter bloqueado |

**Lógica de análisis:**

```
Cada espacio/Enter → _disparar_analisis()
    ↓
¿Cooldown OK? ¿No está ya analizando?
    ↓
Hilo separado → detector.analizar(texto)
    ↓
Si resultado != None → on_alerta(resultado, texto)
```

### `aura/detector.py`
Pipeline de detección. **Única fuente de verdad para las alertas.**

```python
# Flujo de analizar()
def analizar(texto):
    if not groq_key:
        return None           # Sin IA = sin detección
    
    resultado = detectar_groq(texto)
    if resultado: return resultado
    
    resultado = detectar_localhost(texto)
    if resultado: return resultado
    
    return None               # Sin IA disponible = sin alerta
```

**Sanity checks en `detectar_groq()`:**
- Si Groq responde `nivel=SEGURO` pero `score > 0.5` → se corrige a `ADVERTENCIA`
- Si el JSON es inválido → busca `PELIGRO`/`ADVERTENCIA` en el texto crudo
- Si el nivel es desconocido → infiere desde el score

### `aura/scoring.py`
Gestiona el sistema de reputación. Groq evalúa la severidad de cada detección.

**Tabla de puntos:**

| Severidad | Puntos restados | Criterio |
|---|---|---|
| `LEVE` | −5 pts | Insulto menor, tono agresivo |
| `MODERADO` | −15 pts | Bullying claro, ofensa directa |
| `CRITICO` | −30 pts | Amenaza, acoso grave, incitación al odio |

**Consecuencias por score:**

| Score | Estado | Consecuencias |
|---|---|---|
| 80–100 | Excelente | Ninguna |
| 60–79 | Bueno | Ninguna |
| 40–59 | En riesgo | Aviso preventivo |
| ≤ 50 | ⚠️ Alerta crítica | Popup de consecuencias |
| 21–39 | Crítico | Bloqueo de sitios por 3h |
| 1–20 | Muy crítico | Bloqueo 24h, reporte |
| 0 | Bloqueado | Acceso bloqueado completo |

### `aura/site_blocker.py`
Bloquea sitios web editando `C:\Windows\System32\drivers\etc\hosts`.

**Lógica:**
- Cada detección en un sitio se registra
- A la **3ª detección** en el mismo sitio → bloqueo de 3 minutos
- Después de 3 minutos → desbloqueo automático + limpieza del hosts

**Requiere permisos de Administrador.**

Sitios monitoreados: `facebook.com`, `instagram.com`, `twitter.com`, `x.com`, `tiktok.com`, `youtube.com`, `linkedin.com`

---

## Base de Datos

Archivo: `aura_data.db` (SQLite, se crea automáticamente en la raíz del proyecto)

### Esquema

#### `detecciones`
Registra cada evento de ciberbullying detectado.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Auto-incremental |
| `fecha` | TEXT | ISO format: `2025-03-15 18:42:01` |
| `texto` | TEXT | Texto analizado (máx 500 chars) |
| `nivel` | TEXT | `LEVE` / `MODERADO` / `CRITICO` |
| `score_ia` | REAL | Score de Groq (0.0 – 1.0) |
| `fuente` | TEXT | `Groq AI (LLaMA3)` / `Localhost AI` |
| `razon` | TEXT | Explicación de Groq |
| `sugerencia` | TEXT | Cómo reformular el mensaje |
| `sitio` | TEXT | Sitio activo al momento (ej: `facebook.com`) |
| `puntos_rest` | INTEGER | Puntos restados al score |

#### `score_diario`
Score de reputación por día.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | TEXT PK | Fecha ISO (`2025-03-15`) |
| `score` | INTEGER | Score del día (0–100) |
| `detecciones` | INTEGER | Cantidad de detecciones ese día |
| `nivel_dia` | TEXT | Etiqueta textual del nivel |

> El score del día siguiente hereda el score del día anterior.

#### `decisiones`
Registro de lo que el usuario eligió hacer ante cada alerta.

| Columna | Tipo | Descripción |
|---|---|---|
| `deteccion_id` | INTEGER FK | Referencia a `detecciones` |
| `decision` | TEXT | `editar` o `continuar` |
| `tiempo_ms` | INTEGER | Milisegundos que tardó en decidir |

#### `sitios_bloq`
Historial de sitios bloqueados.

| Columna | Tipo | Descripción |
|---|---|---|
| `sitio` | TEXT | Dominio bloqueado |
| `fecha_ini` | TEXT | Inicio del bloqueo |
| `fecha_fin` | TEXT | Fin del bloqueo (vacío si activo) |
| `activo` | INTEGER | `1` = activo, `0` = expirado |

#### `config_store`
Configuración persistente clave-valor.

| Clave | Descripción |
|---|---|
| `groq_key` | API key de Groq |

### Funciones principales de `database.py`

```python
inicializar()                          # Crear tablas + asegurar fila de hoy
get_score_hoy()                        # → int (0-100)
get_score_historico(dias=7)            # → list[dict]
bajar_score(puntos, razon="")          # → int (nuevo score)
registrar_deteccion(texto, nivel, ...) # → int (id)
get_detecciones(limite=50, solo_hoy)   # → list[dict]
get_stats_hoy()                        # → {"total", "criticos", "editados", "score"}
registrar_decision(det_id, decision)   # → None
set_config(clave, valor)               # → None
get_config(clave, default="")          # → str
limpiar_todo()                         # Borra todo el historial
```

---

## Sistema de Puntuación

El score de reputación empieza en **100** y baja con cada detección. Groq determina la severidad de cada evento.

```
Score inicial: 100
    ↓ detección LEVE      → -5  pts → 95
    ↓ detección MODERADO  → -15 pts → 80
    ↓ detección CRITICO   → -30 pts → 50 ← ALERTA CRÍTICA
    ↓ detección CRITICO   → -30 pts → 20 ← BLOQUEO 24H
```

### ¿Cómo Groq determina la severidad?

Se hace una segunda llamada a Groq con el contexto de la detección:

```
Prompt: "Clasifica la severidad: LEVE / MODERADO / CRITICO
         Texto: [texto detectado]
         Nivel: PELIGRO | Score: 0.95 | Razón: [razón de Groq]"

Respuesta: "CRITICO"
```

Si Groq no está disponible, se infiere desde el score IA:
- `score >= 0.85` + `PELIGRO` → CRITICO
- `score >= 0.65` o `PELIGRO` → MODERADO
- resto → LEVE

---

## Pipeline de Detección IA

### Prompt del sistema

```
Eres un sistema de detección de ciberbullying. Analiza el texto y determina 
si contiene acoso, insultos, amenazas o contenido ofensivo.
Responde EXCLUSIVAMENTE con un objeto JSON. Nada más.
```

### Prompt del usuario

```
Texto a analizar: "[texto]"

Clasifica el texto y responde con este JSON:
{
  "nivel": "<SEGURO o ADVERTENCIA o PELIGRO>",
  "score": <0.0 a 1.0>,
  "razon": "<explicación>",
  "sugerencia": "<cómo reformular>"
}

IMPORTANTE:
- PELIGRO si hay insultos directos, amenazas, acoso
- ADVERTENCIA si el tono es agresivo o grosero
- SEGURO SOLO si es completamente inofensivo
- Si dices PELIGRO el score debe ser mayor a 0.6
```

### Modelo usado

`llama-3.1-8b-instant` (Groq) — Temperatura: `0.0` para máxima consistencia.

### Sanity checks automáticos

```python
# Si Groq dice SEGURO pero el score es alto → corregir
if nivel == "SEGURO" and score > 0.5:
    nivel = "ADVERTENCIA"

# Si el JSON falla → buscar palabras clave en el texto crudo
if "PELIGRO" in raw_text:
    return {"nivel": "PELIGRO", "score": 0.9, ...}
```

---

## Interfaz de Usuario

### Dashboard — Vistas

#### 🏠 Home (Reputation Dashboard)
- Score ring animado con el valor actual de la BD
- Métricas: Emotional Impact, Privacy Safety, Community
- Gráfico de estabilidad (últimos 7 días)
- Shield Protection Log con detecciones recientes

#### 💬 Chat Guard
- Simulador de chat con análisis bajo demanda
- Panel lateral con estado del monitor en tiempo real
- Indicadores DLP Active / PII Masking

#### ⚙️ AI Shield
- Configuración de Groq API Key con prueba de conexión
- Estado de las capas de detección (Groq / Localhost)

#### 🔧 Settings
- Toggles de configuración
- Zona de riesgo: limpiar historial

### Popups de alerta

#### Espejo de Empatía (LEVE / MODERADO)
Se muestra cuando se detecta contenido ofensivo no crítico. Incluye:
- Emojis de emoción que muestra cómo se sentiría el receptor
- Texto detectado
- Badge de severidad con puntos restados
- Botón **Reflexionar** con countdown de 5 segundos
- Botón **Enviar de todos modos**

#### Prompt Restricted (CRITICO)
Se muestra para contenido de alto riesgo. Incluye:
- Badge "ASISTENTE PROTECTOR"
- Ícono de advertencia triangular
- Razón de la detección
- Compliance ID único generado
- Botones: **Revisar Prompt** / **Aprender Más**

#### Alerta Score Crítico (score ≤ 50)
Se activa automáticamente cuando el score baja del umbral. Muestra:
- Score actual
- Lista de consecuencias activas según el nivel

### Comportamiento del overlay

Cuando aparece cualquier popup:
1. Overlay negro semitransparente (55-75% opacidad) cubre toda la pantalla
2. `grab_set_global()` bloquea toda interacción con otras ventanas
3. Windows API (`SetForegroundWindow`) fuerza el foco
4. La tecla Enter queda bloqueada via listener separado con `suppress=True`
5. Al elegir una opción → overlay se destruye, Enter se desbloquea

---

## Panel de Debug

Accesible desde el botón **🐛 Debug Panel** en el sidebar.

### Tabs disponibles

| Tab | Contenido |
|---|---|
| **Log en vivo** | Todos los mensajes del sistema con colores por severidad |
| **Detecciones** | Tabla completa de la BD con todos los campos |
| **Score Diario** | Histórico de reputación por día |
| **Sitios Bloq.** | Historial de sitios bloqueados con fechas |
| **SQL Raw** | Ejecutar queries SQL directos contra la BD |

### Interpretando el log

```
[18:46:52] [PIPELINE] Texto recibido: "eres una mierda"
[18:46:52] [GROQ] Enviando a api.groq.com: "eres una mierda"
[18:46:52] [GROQ] Modelo: llama3-8b-8192 | Raw: {"nivel":"PELIGRO"...}
[18:46:52] [GROQ] Resultado: nivel=PELIGRO score=1.0   ← en rojo
[18:46:52] [GROQ] Razon: El texto contiene un insulto grave
[18:46:52] [SCORING] Groq -> severidad: CRITICO (-30 pts)
[18:46:52] [SCORING] Score: 70 (-30 por CRITICO)       ← en amarillo
[18:46:52] [TECLADO] Enter BLOQUEADO                   ← en rojo
```

---

## Bloqueo de Sitios Web

### Cómo funciona

El bloqueo edita el archivo `C:\Windows\System32\drivers\etc\hosts` agregando:

```
127.0.0.1    facebook.com    # AuraEscudoEtico
```

Esto redirige el dominio a `localhost`, haciendo que el sitio sea inaccesible. Después de 3 minutos, la línea se elimina automáticamente y se ejecuta `ipconfig /flushdns`.

### Requisitos

- El programa debe ejecutarse como **Administrador**
- Sin permisos de Admin, el bloqueo se omite (se loguea el aviso)

### Sitios monitoreados

`facebook.com` · `instagram.com` · `twitter.com` · `x.com` · `tiktok.com` · `youtube.com` · `linkedin.com`

Para agregar más sitios, editar `SITIOS_MONITOREADOS` en `aura/site_blocker.py`.

---

## Generar EXE

```bash
# Doble clic en build_exe.bat
# O desde terminal:
build_exe.bat
```

El script instala PyInstaller y todas las dependencias, luego compila a un único EXE en `dist/AuraEscudoEtico.exe`.

### Flags de PyInstaller usados

```bash
--onefile              # Un solo EXE
--windowed             # Sin ventana de consola
--name AuraEscudoEtico
--hidden-import pynput.keyboard._win32
--hidden-import pystray._win32
--collect-all pynput
--collect-all PIL
```

> El EXE detecta automáticamente que está congelado (`sys.frozen`) y no intenta usar `pip`.

---

## Guía de Contribución

### Agregar una nueva plataforma al bloqueo

```python
# aura/site_blocker.py
SITIOS_MONITOREADOS = [
    "facebook.com",
    "nuevo_sitio.com",  # ← agregar aquí
]
```

### Cambiar el modelo de Groq

```python
# aura/detector.py — en detectar_groq()
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",  # ← cambiar aquí (más potente)
    ...
)
```

### Cambiar los umbrales de puntos

```python
# aura/scoring.py
PUNTOS = {
    "LEVE":     5,   # ← editar
    "MODERADO": 15,  # ← editar
    "CRITICO":  30,  # ← editar
}
UMBRAL_ALERTA = 50   # ← score mínimo antes de mostrar consecuencias
```

### Cambiar el cooldown entre análisis

```python
# aura/config.py
CONFIG = {
    "cooldown": 2.5,   # segundos entre llamadas a Groq
}
```

---

## Créditos

Desarrollado para el **Hackathon 8M 2026**  

Equipo: **Group 4**

---

*Aura: Escudo Ético — Porque la prevención del acoso digital comienza antes del envío.*
