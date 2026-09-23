.PHONY: help install preflight build build-full planner backend frontend test test-offline clean deploy-setup deploy-build deploy-run deploy-pull

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## uv sync + dev extras
	uv sync --extra dev

preflight:  ## check env, credenciales, modelos, puertos, sandbox
	uv run python scripts/preflight.py

build:  ## Camino minimo: corrida local completa (todo AgentTool) ->
	uv run python scripts/build_project.py

build-full:  ## Full Team: backend/frontend via A2A (servicios ya levantados)
	BACKEND_AGENT_RESOURCE_NAME=local:8095 FRONTEND_AGENT_RESOURCE_NAME=local:8096 uv run python scripts/build_project.py

planner:  ## Servicio A2A del planner (:8084)
	uv run python -m src.planner_agent.runtime.local_server

backend:  ## Servicio A2A del backend (:8095)
	uv run python -m src.backend_agent.runtime.local_server

frontend:  ## Servicio A2A del frontend (:8096)
	uv run python -m src.frontend_agent.runtime.local_server

test:  ## suite completa (offline: sin red ni GCP)
	uv run --extra dev pytest -q

test-offline:  ## sin deps pesadas; solo las tools deterministas
	uv run --no-project --with pytest python -m pytest tests/test_sandbox.py tests/test_files.py tests/test_mvp.py tests/test_score.py tests/test_process.py tests/test_budget.py tests/test_demo.py -q

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache

deploy-setup:  ## Cloud Run: APIs + SA + Artifact Registry + bucket (una vez)
	bash infra/deploy.sh setup

deploy-build:  ## Cloud Run: compilar y subir las 4 imagenes
	bash infra/deploy.sh build

deploy-run:  ## Cloud Run: job generate-mvp (agentes generan el MVP en GCS)
	bash infra/deploy.sh run

deploy-pull:  ## Cloud Run: bajar el MVP generado y comprimirlo en zip
	bash infra/deploy.sh pull