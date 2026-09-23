"""Tools del Planner Agent.

- Agentes locales (AgentTool): architect, qa, reviewer, docs.
- backend/frontend: via A2A si ``*_AGENT_RESOURCE_NAME`` esta seteado, si no
  como AgentTool local (camino minimo en un solo proceso).
- Deterministicos: ``build_status`` (snapshot del presupuesto + sandbox).
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from google.adk.tools.agent_tool import AgentTool

from src.config import (
    BACKEND_AGENT_RESOURCE_NAME,
    BACKEND_PORT,
    FRONTEND_AGENT_RESOURCE_NAME,
    FRONTEND_PORT,
    MAX_FIX_ITERATIONS,
    MAX_TOKENS_BUDGET,
)
from src.tools.files import list_tree

logger = logging.getLogger(__name__)


def _get_agent_a2a_custom(resource_name: str, default_port: int) -> dict:
    """Resolve A2A endpoint + message URL from a resource name.

    ``local:PORT`` -> local A2A server. Cualquier otra cosa se usa tal cual
    (URL de Cloud Run o resource name de Agent Engine).
    """
    if resource_name.startswith("local"):
        port = resource_name.split(":")[1] if ":" in resource_name else default_port
        return {
            "endpoint": f"http://127.0.0.1:{port}/.well-known/agent-card.json",
            "a2a_url": None,
        }
    return {"endpoint": resource_name, "a2a_url": resource_name}


def build_status() -> dict[str, Any]:
    """Estado deterministico para que el planner decida iteraciones/presupuesto."""
    tree = list_tree()
    return {
        "max_fix_iterations": MAX_FIX_ITERATIONS,
        "max_tokens_budget": MAX_TOKENS_BUDGET,
        "sandbox_file_count": tree["file_count"],
        "sandbox_files": [f["path"] for f in tree["files"]][:25],
        "backend_mode": "a2a" if BACKEND_AGENT_RESOURCE_NAME else "local",
        "frontend_mode": "a2a" if FRONTEND_AGENT_RESOURCE_NAME else "local",
    }


def _local_agent_tool(module_path: str, name: str):
    module = importlib.import_module(module_path)
    return AgentTool(agent=module.root_agent, name=name)


def _builder_tool(name: str, resource_name: str, default_port: int, description: str, module_path: str):
    if resource_name:
        from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

        config = _get_agent_a2a_custom(resource_name, default_port)
        remote = RemoteA2aAgent(
            name=name,
            description=description,
            agent_card=config["endpoint"],
            a2a_url=config["a2a_url"],
        )
        return AgentTool(agent=remote, name=name)
    return _local_agent_tool(module_path, name)


def get_tools() -> list:
    """Assemble the planner tools (local sub-agents + optional A2A builders)."""
    from google.adk.tools.function_tool import FunctionTool
    from google.adk.tools.preload_memory_tool import PreloadMemoryTool

    tools = [PreloadMemoryTool(), FunctionTool(func=build_status)]

    tools.append(_local_agent_tool("src.architect_agent.agent", "architect_agent"))
    tools.append(_local_agent_tool("src.qa_agent.agent", "qa_agent"))
    tools.append(_local_agent_tool("src.reviewer_agent.agent", "reviewer_agent"))
    tools.append(_local_agent_tool("src.docs_agent.agent", "docs_agent"))

    tools.append(
        _builder_tool(
            "backend_agent",
            BACKEND_AGENT_RESOURCE_NAME,
            BACKEND_PORT,
            (
                "Backend Agent - implementa el pipeline de audio/transcripcion/traduccion "
                "y el servidor multi-sesion del producto generado. Escribe SOLO en <out>/backend/."
            ),
            "src.backend_agent.agent",
        )
    )
    tools.append(
        _builder_tool(
            "frontend_agent",
            FRONTEND_AGENT_RESOURCE_NAME,
            FRONTEND_PORT,
            (
                "Frontend Agent - implementa la vista de audiencia (selector de sesion e "
                "idioma, subtitulos en vivo). Escribe SOLO en <out>/frontend/."
            ),
            "src.frontend_agent.agent",
        )
    )

    return tools