"""Local A2A server del Planner Agent.

Usage: uv run python -m src.planner_agent.runtime.local_server
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")

import logging  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")

import uvicorn  # noqa: E402
from a2a.server.apps import A2AStarletteApplication  # noqa: E402
from a2a.server.request_handlers import DefaultRequestHandler  # noqa: E402
from a2a.server.tasks import InMemoryTaskStore  # noqa: E402
from a2a.types import TransportProtocol  # noqa: E402

from src.config import PLANNER_PORT

AGENT_HOST = os.environ.get("HOST", "0.0.0.0")  # Cloud Run exige 0.0.0.0
AGENT_PORT = int(os.environ.get("PORT") or os.environ.get("PLANNER_PORT", PLANNER_PORT))
PUBLIC_URL = os.environ.get("AGENT_PUBLIC_URL", f"http://127.0.0.1:{AGENT_PORT}")


async def run_server():
    from .agent_card import create_planner_card
    from .agent_executor import PlannerExecutor

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project and not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("Se necesita GOOGLE_CLOUD_PROJECT (Vertex) o GEMINI_API_KEY. Ver .env")

    print("=" * 60)
    print("Planner Agent (orquestador) A2A server")
    print(f"Mode: backend={'a2a' if os.environ.get('BACKEND_AGENT_RESOURCE_NAME') else 'local'} "
          f"frontend={'a2a' if os.environ.get('FRONTEND_AGENT_RESOURCE_NAME') else 'local'}")
    print("El agente (ADK/vertexai) se inicializa al recibir el primer task.")
    print("=" * 60)

    card = create_planner_card()
    card.url = PUBLIC_URL
    card.preferred_transport = TransportProtocol.jsonrpc

    executor = PlannerExecutor()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)

    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    inner = app.build()
    outer = Starlette(
        routes=[
            Route("/", endpoint=lambda _: JSONResponse({"status": "ok"}), methods=["GET"]),
            Mount("/", app=inner),
        ]
    )

    config = uvicorn.Config(outer, host=AGENT_HOST, port=AGENT_PORT, log_level="info", loop="none")

    print(f"Planner A2A: http://{AGENT_HOST}:{AGENT_PORT}")
    print(f"Agent card:  {PUBLIC_URL}/.well-known/agent-card.json")
    print("=" * 60)
    print("Los imports pesados (ADK/vertexai) se cargan recien en el primer task.")
    print(f"Bindeando 0.0.0.0:{AGENT_PORT} (PORT={os.environ.get('PORT')})...")
    print("=" * 60)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())