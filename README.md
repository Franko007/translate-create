# vibeathon-builder-agents

**Nivel 1** de la solución para la Vibeathon Nerdearla 2026: un sistema de
agentes **constructores** (Google ADK + A2A) cuyo único trabajo es **generar el
código** del MVP de transcripción y traducción simultánea en la carpeta de
salida. Los agentes resuelven el problema; este repositorio solo los hace
capaces.

Hay dos niveles y no se mezclan:

| Nivel | Qué es | Quién lo produce |
|---|---|---|
| **1 (este repo)** | El sistema multiagente que planifica, escribe, prueba, revisa y documenta | Vos ahora (ya está acá) |
| **2 (el MVP)** | Solución open source de transcripción/traducción simultánea | Los agentes de este repo cuando los ejecutes |

## Agentes

| Agente | Rol | Conexión |
|---|---|---|
| `planner_agent` | Orquestador: lee el brief, arma tareas, lanza y controla iteraciones | Entrada (A2A o local) |
| `architect_agent` | Escribe los contratos en `<out>/spec/` antes que cualquier código | `AgentTool` local |
| `backend_agent` | Implementa pipeline de audio/transcripción/traducción + servidor multi-sesión | **A2A** (Cloud Run) o local |
| `frontend_agent` | Implementa la vista de audiencia (sesión + idioma + subtítulos) | **A2A** (Cloud Run) o local |
| `qa_agent` | Escribe y ejecuta tests, corre la demo, reporta fallas | `AgentTool` local |
| `reviewer_agent` | Puntúa contra MV0 del jurado y checklist MVP | `AgentTool` local |
| `docs_agent` | README, RUNBOOK, guion demo y checklist Devpost del producto | `AgentTool` local |

## Uso rápido (camino mínimo)

```bash
uv sync --extra dev
cp .env.example .env          # pega: GEMINI_API_KEY o credenciales Vertex
uv run python scripts/build_project.py
```

Eso genera el proyecto final bajo `generated/nerdearla-subtitles/` con el
pipeline de punta a punta. Para ver cada agente por separado como servicio A2A
(Cloud Run), ver `docs/HOW_TO_RUN.md`.

- Guia de diseño completa: `vibeathon_builder_agents_prompt.md`
- Brief del producto que los agentes reciben: `spec/PRODUCT_BRIEF.md`

Licencia: Apache 2.0. Ver `NOTICE`.