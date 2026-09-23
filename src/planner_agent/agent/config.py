"""Configuration for the Planner Agent (orquestador)."""

from src.config import AGENT_MODELS

AGENT_NAME = "planner_agent"
AGENT_DESCRIPTION = (
    "Planner Agent - orquestador de los agentes constructores. Lee el brief desde "
    "spec/PRODUCT_BRIEF.md, descompone el trabajo en tareas, lanza a architect, "
    "backend, frontend, qa, reviewer y docs, y controla el presupuesto de "
    "iteraciones y de tokens. Recibe la orden del usuario y devuelve el BuildReport."
)
MODEL = AGENT_MODELS[AGENT_NAME]