"""Local A2A server del Frontend Agent.

Usage: uv run python -m src.frontend_agent.runtime.local_server
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

from src.config import FRONTEND_PORT

AGENT_PORT = int(os.environ.get("FRONTEND_PORT", FRONTEND_PORT))


async def run_server():
    from .agent_card import create_frontend_card
    from .agent_executor import FrontendExecutor

    from ..agent import root_agent

    print("Frontend Agent A2A server (implementa la vista de audiencia)")

    card = create_frontend_card()
    card.url = f"http://127.0.0.1:{AGENT_PORT}"
    card.preferred_transport = TransportProtocol.jsonrpc

    executor = FrontendExecutor()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)
    config = uvicorn.Config(app.build(), host="127.0.0.1", port=AGENT_PORT, log_level="info", loop="none")

    print(f"Frontend A2A: http://127.0.0.1:{AGENT_PORT}")
    print(f"Agent card:   http://127.0.0.1:{AGENT_PORT}/.well-known/agent-card.json")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())