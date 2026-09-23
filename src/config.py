"""Shared configuration for the builder agents (Nivel 1)."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# Carpetas de salida (Nivel 2). TODO lo que generan los agentes vive dentro.
OUT_DIR = Path(os.environ.get("OUT_DIR", PACKAGE_ROOT / "generated" / "nerdearla-subtitles")).expanduser()
if not OUT_DIR.is_absolute():
    OUT_DIR = (PACKAGE_ROOT / OUT_DIR).resolve()

# Control de la corrida
MAX_FIX_ITERATIONS = int(os.environ.get("MAX_FIX_ITERATIONS", "3"))
MAX_TOKENS_BUDGET = int(os.environ.get("MAX_TOKENS_BUDGET", "200000"))
APPROVAL_MODE = os.environ.get("APPROVAL_MODE", "ask").lower()  # yes | no | ask
RUN_TIMEOUT_S = int(os.environ.get("RUN_TIMEOUT_S", "120"))

# Modelos por agente (env-configurables, sin hardcodear nombres).
DEFAULT_MODEL = "gemini-3.1-flash-lite"
CODEGEN_MODEL = "gemini-3.5-flash"
AGENT_MODELS = {
    "planner_agent": os.environ.get("PLANNER_MODEL", DEFAULT_MODEL),
    "architect_agent": os.environ.get("ARCHITECT_MODEL", DEFAULT_MODEL),
    "backend_agent": os.environ.get("BACKEND_MODEL", CODEGEN_MODEL),
    "frontend_agent": os.environ.get("FRONTEND_MODEL", CODEGEN_MODEL),
    "qa_agent": os.environ.get("QA_MODEL", DEFAULT_MODEL),
    "docs_agent": os.environ.get("DOCS_MODEL", DEFAULT_MODEL),
    "reviewer_agent": os.environ.get("REVIEWER_MODEL", DEFAULT_MODEL),
}


def agent_model(name: str) -> str:
    return AGENT_MODELS.get(name, DEFAULT_MODEL)


# Puertos de los servicios A2A
PLANNER_PORT = int(os.environ.get("PLANNER_PORT", "8084"))
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8095"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "8096"))

# Nombres de recurso para redirigir a servicios A2A remotos (Cloud Run).
# Si no se setean, los agentes se usan como AgentTool local (mismo proceso).
BACKEND_AGENT_RESOURCE_NAME = os.environ.get("BACKEND_AGENT_RESOURCE_NAME", "")
FRONTEND_AGENT_RESOURCE_NAME = os.environ.get("FRONTEND_AGENT_RESOURCE_NAME", "")

# El producto generado debe exponer este entrypoint de demo (contrato).
DEMO_ENTRY = "demo/main.py"