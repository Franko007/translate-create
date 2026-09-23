"""Configuration for the Architect Agent."""

from src.config import AGENT_MODELS

AGENT_NAME = "architect_agent"
AGENT_DESCRIPTION = (
    "Architect Agent - produce los CONTRATOS antes de que se escriba codigo: "
    "arquitectura, presupuesto de latencia por etapa, estructura de carpetas, "
    "interfaces entre modulos y esquema de mensajes. Escribe SOLO en <out>/spec/."
)
MODEL = AGENT_MODELS[AGENT_NAME]