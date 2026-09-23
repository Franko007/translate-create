"""Configuration for the QA Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "qa_agent"
AGENT_DESCRIPTION = (
    "QA Agent - escribe y EJECUTA los tests del producto generado y corre la "
    "demo de 2+ sesiones (run_demo). Reporta fallas con logs concretos para que "
    "los agentes implementadores corrijan. Escribe SOLO en <out>/tests/ y <out>/demo/."
)
MODEL = AGENT_MODELS[AGENT_NAME]