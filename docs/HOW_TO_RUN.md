# HOW TO RUN — Nivel 1

## 0. Requisitos

- Python 3.11+ y `uv` en PATH.
- Credenciales: `GEMINI_API_KEY` (default) **o** Vertex (`GOOGLE_CLOUD_PROJECT`
  + `GOOGLE_CLOUD_LOCATION=global`). Copia `.env.example` a `.env`.

```bash
uv sync --extra dev
uv run python scripts/preflight.py   # valida entorno y credenciales
```

## 1. Camino mínimo (todo local, un solo proceso)

```bash
uv run python scripts/build_project.py
```

- backend_agent y frontend_agent corren como `AgentTool` local (misma maquina).
- El resultado se escribe en `generated/nerdearla-subtitles/`.
- El informe: `generated/nerdearla-subtitles/.build_logs/build_report.md`.
- Con `APPROVAL_MODE=ask` (default) los comandos de qa que necesiten aprobacion
  se frenan con `needs_human_approval`. Setea `approval_mode=yes` para headless.

## 2. Topología completa (backend/frontend como A2A)

Levantá cada agente como servicio A2A (puertos por defecto 8084/8095/8096):

```bash
uv run make frontend    # terminal 1 -> :8096
uv run make backend     # terminal 2 -> :8095
uv run make planner     # terminal 3 -> :8084 (entrada A2A)
```

Después el build en modo A2A:

```bash
make build-full
```

`BACKEND_AGENT_RESOURCE_NAME=local:8095` y `FRONTEND_AGENT_RESOURCE_NAME=local:8096`
redirigen a esos servicios. En Cloud Run pasá la URL del agente card en el mismo
env var y el planner lo contacta remotamente.

## 3. Tests

```bash
make test-offline      # tools deterministicas, sin red ni GCP
make test              # suite completa (requiere deps)
```

## 4. Configuración

| Env | Default | Qué controla |
|---|---|---|
| `OUT_DIR` | `generated/nerdearla-subtitles` | Dónde generan los agentes (sandbox) |
| `MAX_FIX_ITERATIONS` | `3` | Tope del bucle de correcciones reviewer→implementadores |
| `MAX_TOKENS_BUDGET` | `200000` | Presupuesto de tokens de la corrida |
| `APPROVAL_MODE` | `ask` | `yes`\|`no`\|`ask` para comandos sensibles |
| `RUN_TIMEOUT_S` | `120` | Timeout de comandos y demo |
| `PLANNER_MODEL` / `*` | por rol | Modelos por agente (backend/frontend usan el de codegen) |
| `BACKEND_AGENT_RESOURCE_NAME` | vacío | `local:8095` o URL de Cloud Run del backend |
| `FRONTEND_AGENT_RESOURCE_NAME` | vacío | `local:8096` o URL de Cloud Run del frontend |

## 5. GCP (Cloud Run)

Cada agente que quieras servir puede deployarse como servicio Cloud Run con su
A2A server (`src/<agente>/runtime/local_server.py` es el mismo código que
corre el contenedor). Build tips en `docs/GOTCHAS.md`.