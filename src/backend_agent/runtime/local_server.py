"""Local A2A server del Backend Agent.

Usage: uv run python -m src.backend_agent.runtime.local_server
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

from src.config import BACKEND_PORT

AGENT_PORT = int(os.environ.get("BACKEND_PORT", BACKEND_PORT))


async def run_server():
    from .agent_card import create_backend_card
    from .agent_executor import BackendExecutor

    from ..agent import root_agent

    print("Backend Agent A2A server (implementa el pipeline backend)")

    card = create_backend_card()
    card.url = f"http://127.0.0.1:{AGENT_PORT}"
    card.preferred_transport = TransportProtocol.jsonrpc

    executor = BackendExecutor()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)
    config = uvicorn.Config(app.build(), host="127.0.0.1", port=AGENT_PORT, log_level="info", loop="none")

    print(f"Backend A2A: http://127.0.0.1:{AGENT_PORT}")
    print(f"Agent card:  http://127.0.0.1:{AGENT_PORT}/.well-known/agent-card.json")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())