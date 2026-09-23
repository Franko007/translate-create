"""Configuration for the Backend Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "backend_agent"
AGENT_DESCRIPTION = (
    "Backend Agent - implementa la ingesta de audio, VAD/chunking, el pipeline "
    "de transcripcion y traduccion, los proveedores de modelos (Gemini/local) y "
    "el servidor multi-sesion (WebSocket/SSE). Escribe SOLO en <out>/backend/."
)
MODEL = AGENT_MODELS[AGENT_NAME]