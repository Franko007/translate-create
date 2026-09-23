# Prompt: Sistema de agentes "constructores" (Google ADK + A2A) que generan el MVP de la Vibeathon Nerdearla 2026

## Rol

Sos un ingeniero/a senior en Python con experiencia en **Google ADK (Agent Development Kit)**, el **protocolo A2A**, Gemini y sistemas multiagente para generación de código. Vas a construir un **sistema de agentes** que yo voy a ejecutar después para que **generen el proyecto final** de una hackathon.

## 0. Aclaración importante: dos niveles

Hay **dos productos distintos** y no hay que mezclarlos:

| Nivel | Qué es | Quién lo produce |
|---|---|---|
| **Nivel 1: el sistema de agentes constructores** | Un proyecto multiagente (ADK + A2A) cuyos agentes planifican, escriben código, prueban, revisan y documentan | **Vos, en esta conversación** |
| **Nivel 2: el proyecto final (el MVP de la vibeathon)** | Una solución open source de transcripción y traducción simultánea de conferencias | **Los agentes del Nivel 1, cuando yo los ejecute** |

**Tu entregable ahora es el Nivel 1.** Los agentes deben recibir como entrada el brief del producto (Sección 6) y producir como salida un repositorio completo del Nivel 2 en una carpeta de salida (por ejemplo `./generated/nerdearla-subtitles/`).

---

## 1. Repositorio de referencia (patrón de arquitectura)

Tomá como referencia el **estilo de arquitectura y de repositorio** de:
`https://github.com/jorgeucano/Multi-Agent-Marathon-Planner-Workshop`

Replicá el **patrón**:

- Agente orquestador + agentes especializados con Google ADK, cada uno con su `instruction.md`, modelo configurable por variable de entorno y herramientas propias.
- **`AgentTool`** para capacidades locales (mismo proceso) y **A2A / JSON-RPC** para agentes que corren como servicio separado (`agent_card`, `agent_executor`, `local_server`).
- **Herramientas determinísticas** para todo lo que no debe decidir el LLM (escribir archivos, correr tests, chequear el checklist). El LLM decide y redacta; el código ejecuta y mide.
- **Skills** en carpetas (`SKILL.md` + `tools.py`).
- Ergonomía: `uv` + `pyproject.toml`, `.env.example`, `Makefile`, `scripts/preflight.py`, un cliente CLI que ejercita el sistema de punta a punta, tests **offline** (sin red ni GCP), `docs/GOTCHAS.md`, licencia Apache 2.0.

**No copies código literal ni nada del dominio "maratón".** Si reutilizás alguna pieza, mantené la atribución y el `NOTICE` (Apache 2.0).

---

## 2. Los agentes constructores

Diseñá estos agentes (podés fusionar o dividir si lo justificás):

| Agente | Responsabilidad | Conexión |
|---|---|---|
| `planner_agent` | Orquestador. Lee el brief, descompone el trabajo en tareas con dependencias, decide el orden, lanza a los demás y controla el presupuesto de iteraciones y de tiempo | Punto de entrada |
| `architect_agent` | Produce los **contratos** antes de que se escriba código: arquitectura, presupuesto de latencia por etapa, estructura de carpetas, interfaces entre módulos, esquemas de mensajes | `AgentTool` local |
| `backend_agent` | Implementa ingesta de audio, VAD/chunking, pipeline de transcripción y traducción, proveedores de modelos (Gemini y local), servidor WebSocket/SSE, gestión de múltiples sesiones | **A2A** (servicio separado; corre en paralelo con el frontend) |
| `frontend_agent` | Implementa la vista de audiencia: selector de sesión e idioma, subtítulos en vivo, panel de monitoreo | **A2A** (servicio separado) |
| `qa_agent` | Escribe y **ejecuta** tests, corre el proyecto generado con audios de prueba y 2+ sesiones, reporta fallas con logs concretos para que los agentes corrijan | `AgentTool` local |
| `docs_agent` | README, `GOTCHAS.md`, `RUNBOOK.md`, guion del video demo (1–2 min) y checklist de entrega para Devpost | `AgentTool` local |
| `reviewer_agent` | Estilo `evaluator_agent` del repo: puntúa el proyecto generado contra los criterios del jurado y el checklist del MVP; devuelve scores comparables y una lista priorizada de correcciones | `AgentTool` local |

### Coordinación entre agentes: contract-first

Para evitar que `backend_agent` y `frontend_agent` se pisen al trabajar en paralelo:

1. `architect_agent` escribe primero en `<out>/spec/`: `ARCHITECTURE.md`, `INTERFACES.md` (contratos entre módulos), `MESSAGE_SCHEMA.json` (formato del mensaje de subtítulo: `session_id`, `lang`, `text`, `is_final`, `t_audio_in`, `t_emitted`, etc.) y `tasks.json`.
2. Cada agente implementador solo escribe dentro de **su propia carpeta** asignada y respeta esos contratos.
3. Si un agente necesita cambiar un contrato, lo pide al `planner_agent` (no lo edita por su cuenta).

### Flujo de ejecución (pipeline con bucle de corrección)

```
brief ─► planner ─► architect (contratos)
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
        backend (A2A)        frontend (A2A)      ← en paralelo
             └──────────┬──────────┘
                        ▼
                    qa (corre tests + demo)
                        ▼
                 reviewer (scores + checklist)
                        ▼
        ¿pasa el umbral? ── no ──► planner reasigna correcciones (máx. N iteraciones)
                        │ sí
                        ▼
                  docs ─► checklist final ─► informe
```

---

## 3. Herramientas determinísticas (obligatorias)

Implementalas como funciones de Python que los agentes invocan; el LLM **no** ejecuta nada directamente fuera de ellas.

- `write_file(path, content)`: **solo** dentro de la carpeta de salida (rechazar rutas fuera del sandbox, `..`, enlaces simbólicos).
- `read_file`, `list_tree`, `apply_patch`.
- `run_command(cmd)`: con **lista blanca** (por ejemplo `uv sync`, `uv run pytest`, `ruff`, `python -m ...`), con timeout y captura de stdout/stderr. Sin `rm -rf`, sin acceso a rutas fuera del sandbox.
- `run_demo(sessions=2)`: levanta el proyecto generado, emite audios de prueba en 2+ sesiones simultáneas y devuelve métricas (latencia por etapa, errores).
- `check_mvp_checklist()`: verificación **determinística** de los requisitos mínimos (Sección 6.3): licencia OSI presente, `README.md` con secciones obligatorias, `.env.example`, audios de prueba en `samples/`, test de 2 sesiones simultáneas, `LICENSE`, exportador SRT/VTT, ausencia de secretos hardcodeados (escáner de claves).
- `score_project()`: combina reglas determinísticas con un juez LLM para calidad de documentación y claridad de despliegue.

### Seguridad y control (no negociable)

- Todo el código generado vive en `<out>/`; nada se escribe fuera.
- **Puertas de aprobación humana** configurables (`--approve-each-stage`) antes de ejecutar comandos o instalar dependencias.
- **Tope de iteraciones** del bucle de corrección y **tope de tokens/costo** por corrida, configurables por variable de entorno; al superarlos, el sistema se detiene y reporta.
- Log completo y reproducible de cada acción de cada agente en `<out>/.build_logs/`.
- Nunca imprimir ni guardar credenciales. Todo por variables de entorno.

---

## 4. Estructura del repositorio del Nivel 1

```
src/
  config.py
  planner_agent/
    agent/        instruction.md, tools, agent
    runtime/      agent_card, agent_executor, local_server
  architect_agent/
  backend_agent/
    agent/        instruction.md, tools
    runtime/      agent_card, agent_executor, local_server    (servicio A2A)
  frontend_agent/
    runtime/      ...                                          (servicio A2A)
  qa_agent/
  docs_agent/
  reviewer_agent/
    metrics/      criterios del jurado + checklist MVP
  tools/          write_file, run_command, run_demo, check_mvp_checklist, score_project
spec/
  PRODUCT_BRIEF.md     (contenido de la Sección 6; es la entrada de los agentes)
scripts/
  preflight.py         verifica credenciales, modelos, puertos, sandbox
  build_project.py     CLI principal: python scripts/build_project.py --out ./generated/nerdearla-subtitles
tests/                 suite offline con un LLM falso (sin red ni GCP)
docs/
  GOTCHAS.md
  HOW_TO_RUN.md
Makefile, pyproject.toml, .env.example, LICENSE, NOTICE, README.md
```

### Configuración

- Variables por agente: `PLANNER_MODEL`, `ARCHITECT_MODEL`, `BACKEND_MODEL`, `FRONTEND_MODEL`, `QA_MODEL`, `DOCS_MODEL`, `REVIEWER_MODEL`. No hardcodees nombres de modelo; verificá en la documentación vigente cuáles existen.
- Dos modos de credenciales: **Gemini API con API key** (por defecto) y **Vertex AI** (`GOOGLE_GENAI_USE_VERTEXAI=true`).
- `MAX_FIX_ITERATIONS`, `MAX_TOKENS_BUDGET`, `APPROVAL_MODE`.

---

## 5. Lo que necesito de vos (por etapas; esperá mi confirmación entre etapas)

1. **Diseño del sistema de agentes**: diagrama en texto, contratos entre agentes, criterios de "terminado", estrategia de paralelismo y de corrección.
2. **Plan de trabajo** para construir el Nivel 1 rápido (ver Sección 7 sobre el tiempo).
3. **Implementación** completa del Nivel 1: agentes, `instruction.md` de cada uno (con ejemplos de salida esperada), herramientas, CLI, tests offline.
4. **`spec/PRODUCT_BRIEF.md`** con el brief de la Sección 6 tal cual.
5. **README y `HOW_TO_RUN.md`** con los comandos exactos para que yo lo ejecute.
6. **Una corrida de ejemplo** descripta paso a paso: qué debería verse en el log, qué archivos aparecen en `<out>/` y en qué orden.

---

## 6. Brief del producto que los agentes deben construir (Nivel 2)

> Este contenido es la **entrada** de los agentes. Guardalo como `spec/PRODUCT_BRIEF.md`.

### 6.1 Contexto

Nerdearla quiere que su evento sea lo más accesible posible y ofrece transcripción simultánea al español. Hoy usa herramientas comerciales (español → español e inglés → español). Este año hay **más de 30 sesiones en inglés, muchas en simultáneo**, y esa solución no escala: es cara, depende de operación manual y no se replica en otros eventos. Objetivo: **la mejor solución abierta** para que las conferencias open source sean accesibles (no reemplazar a los intérpretes humanos en todos los contextos).

### 6.2 El desafío

Construir una **solución open source de transcripción simultánea a escala**:

- Tomar audio en vivo (p. ej. el stream de un escenario) y producir **subtítulos en tiempo real**: transcripción en el idioma original y traducción al español (y, si se puede, de español a inglés).
- Correr **varias sesiones en paralelo** (5, 10 o más escenarios).
- Licencia aprobada por la OSI y documentación clara para que cualquier conferencia la despliegue.
- **Vista para la audiencia**: web o app donde cada persona elige sesión e idioma.

Recomendación de los organizadores: construir sobre las capacidades de audio de **Gemini**; para correr 100% local, usar **Gemma**.

### 6.3 Requisitos mínimos (MVP) — el `reviewer_agent` los usa como checklist

1. Recibir audio en vivo de **al menos una fuente** (micrófono, archivo o stream), con audios de prueba en el repo y una opción sencilla para probarlo importándolos.
2. **Transcripción en tiempo real** del idioma original (español o inglés).
3. **Traducción en tiempo real de inglés a español**.
4. **Mostrar los subtítulos** (web, overlay, terminal, etc.).
5. Procesar **al menos dos sesiones en simultáneo** y explicar en el README **cómo escalar a más**.
6. Repositorio con licencia OSI (Apache 2.0 o MIT) y README que explique cómo levantarlo y qué credenciales o modelos necesita.

### 6.4 Opcionales (priorizar por impacto/esfuerzo)

Exportar transcripción a SRT/VTT/texto al final de cada charla; glosario de términos técnicos y nombres propios; panel de monitoreo (estado por sesión, latencia, errores); integración con OBS/vMix; portugués y más idiomas.

### 6.5 Criterios del jurado (el `reviewer_agent` puntúa cada uno)

| Criterio | Pregunta |
|---|---|
| **Calidad** | ¿La transcripción es precisa y se entiende, incluso con términos técnicos? |
| **Latencia** | ¿Los subtítulos aparecen con un retraso aceptable para seguir una charla en vivo? |
| **Escalabilidad** | ¿Corre muchas sesiones en simultáneo sin grandes cambios ni costos prohibitivos? |
| **Despliegue y operación** | ¿Qué tan sencilla es la puesta en producción y la operación durante un evento? |
| **Innovación** | ¿Hay funcionalidades creativas que aporten valor extra? |

### 6.6 Decisiones de diseño que el `architect_agent` debe respetar en el producto

- **Camino caliente directo**: audio → subtítulo va por un pipeline de streaming por sesión (ingesta → VAD/chunking → modelo de audio de Gemini, idealmente vía Live API → traducción → WebSocket/SSE). **No** debe pasar por un orquestador LLM ni por saltos entre agentes por cada fragmento: la latencia es un criterio del jurado.
- **Resultados parciales y finales**, y medición de latencia en cada etapa.
- **Aislamiento de sesiones**: si una falla, las demás siguen; reintentos con backoff.
- **Escalado horizontal** documentado: más procesos worker + Redis pub/sub opcional; modo en memoria sin Redis para probar rápido.
- **Interfaz de proveedor intercambiable**: Gemini (por defecto) y local (Gemma/Whisper).
- **Dos modos de credenciales**: Gemini API con API key y Vertex AI.
- Stack sugerido: Python 3.11+, `uv`, FastAPI, frontend liviano (HTML/JS), Docker/docker compose, `LICENSE` Apache 2.0 o MIT.
- Documentación y UI en español, con soporte de inglés. Honestidad sobre límites (idiomas, latencia observada, costo aproximado por sesión).

### 6.7 Reglas de la vibeathon que el producto generado debe cumplir

- Debe construirse durante la vibeathon (24 y 25 de septiembre de 2026); se pueden usar librerías, modelos y servicios existentes (Gemini, Gemma, Whisper, etc.), pero la solución en sí debe ser propia.
- Video demo de 1–2 minutos en YouTube con audio real de una charla (sirve cualquier charla de ediciones anteriores de Nerdearla); idealmente con subtítulos en inglés hechos con el propio proyecto.
- Repositorio público con README que explique cómo levantarlo y qué credenciales o modelos necesita.
- Envío por Devpost antes del **25 de septiembre de 2026, 15:00 UTC (12:00 en Argentina)**.

---

## 7. Restricción de tiempo (leer antes de diseñar)

El plazo de la vibeathon es de aproximadamente 24 horas y el sistema de agentes es **infraestructura previa**, no el producto que evalúa el jurado. Por eso:

- Diseñá el Nivel 1 para que sea **construible en pocas horas**: prefiero pocos agentes bien hechos antes que muchos a medias.
- Si alguna pieza del Nivel 1 no es esencial (por ejemplo, A2A entre `backend_agent` y `frontend_agent`), ofrecé una **variante simplificada** (todo con `AgentTool` local) y dejá A2A como mejora.
- Priorizá que **una corrida completa produzca un MVP que arranque** antes que perfeccionar el bucle de corrección.
- Indicá claramente cuál es el **camino mínimo** para llegar a un MVP funcional si el tiempo se acaba.

---

## 8. Primera tarea

Empezá por los puntos **1 (diseño del sistema de agentes)** y **2 (plan de trabajo)**. Al final, listá las decisiones que necesitás que yo tome (por ejemplo: modo API key vs. Vertex AI, si usamos A2A real o `AgentTool` local para ganar tiempo, cuánta aprobación humana quiero entre etapas, y qué charla de Nerdearla usamos como audio de demo).
