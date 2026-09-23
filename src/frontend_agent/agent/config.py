"""Configuration for the Frontend Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "frontend_agent"
AGENT_DESCRIPTION = (
    "Frontend Agent - implementa la vista de audiencia del producto generado: "
    "selector de sesion e idioma, subtitulos en vivo por WebSocket/SSE y un "
    "panel de monitoreo de latencia. Escribe SOLO en <out>/frontend/."
)
MODEL = AGENT_MODELS[AGENT_NAME]