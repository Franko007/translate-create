"""Configuration for the Docs Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "docs_agent"
AGENT_DESCRIPTION = (
    "Docs Agent - produce la documentacion de entrega del producto generado: "
    "README, RUNBOOK, GOTCHAS, guion del video demo (1-2 min) y checklist Devpost. "
    "Escribe SOLO en <out>/docs/ y en la raiz de <out>/ (scope 'root' para README/LICENSE/.env.example)."
)
MODEL = AGENT_MODELS[AGENT_NAME]