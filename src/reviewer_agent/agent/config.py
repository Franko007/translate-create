"""Configuration for the Reviewer Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "reviewer_agent"
AGENT_DESCRIPTION = (
    "Reviewer Agent - puntua el proyecto generado contra los criterios del jurado "
    "y el checklist del MVP. Usa check_mvp_checklist() y score_project() (ambos "
    "deterministicos) y agrega juicio LLM: scores comparables y lista priorizada "
    "de correcciones."
)
MODEL = AGENT_MODELS[AGENT_NAME]