# Build multi-target para Cloud Run (servicios A2A + job generador).
#
#   planner/backend/frontend: servicios A2A que escuchan en $PORT (0.0.0.0)
#   job: corre scripts/build_project.py (genera el MVP en $OUT_DIR, por
#        default sobre un volumen GCS montado).
#
# Ejemplo:
#   docker build --target planner -t planner:latest .

FROM python:3.12-slim AS agent-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir "uv>=0.5,<1"

WORKDIR /app

COPY pyproject.toml README.md NOTICE ./
COPY src ./src
COPY scripts ./scripts
COPY spec ./spec
COPY LICENSE ./
COPY .env.example ./

# Corre ignore-deps: los agentes que NO corren Vertex (build local) siguen teniendo
# la suite de tools deterministas sin depender de credenciales.
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# --- Servicios A2A (Cloud Run: 1 request por instancia; ver infra/run.yaml) ---
FROM agent-base AS planner
CMD ["python", "-m", "src.planner_agent.runtime.local_server"]

FROM agent-base AS backend
CMD ["python", "-m", "src.backend_agent.runtime.local_server"]

FROM agent-base AS frontend
CMD ["python", "-m", "src.frontend_agent.runtime.local_server"]

# --- Job generador del MVP (Cloud Run Job; ver infra/job.yaml) ---
FROM agent-base AS job
CMD ["python", "scripts/build_project.py"]