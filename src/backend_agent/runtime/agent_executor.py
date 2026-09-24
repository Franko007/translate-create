"""A2A Agent Executor for the Backend Agent.

Imports pesados (vertexai, google.adk) diferidos a ``_init_agent`` (primer
request): el container bindea el puerto rapido y sobrevive el startup probe.
"""

import json
import logging
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError

logger = logging.getLogger(__name__)


def _extract_text(parts) -> str:
    chunks = []
    for p in parts or []:
        if hasattr(p, "text") and p.text:
            chunks.append(p.text)
        elif hasattr(p, "function_call") and p.function_call and p.function_call.args:
            chunks.append(json.dumps(p.function_call.args, ensure_ascii=False))
    return "".join(chunks)


class BackendExecutor(AgentExecutor):
    def __init__(self):
        self.agent = None
        self.runner = None

    def _init_agent(self) -> None:
        import vertexai
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService

        if self.agent is None:
            from ..agent import root_agent
            self.agent = root_agent

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            vertexai.init(
                project=project_id,
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            )
        if self.runner is None:
            self.runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                session_service=InMemorySessionService(),
            )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if self.agent is None:
            self._init_agent()
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not hasattr(context, "current_task") or not context.current_task:
            await updater.submit()
        await updater.start_work()
        request_data = context.get_user_input()
        if not request_data:
            await updater.update_status(TaskState.failed, message=new_agent_text_message("No data"), final=True)
            return
        try:
            from google.genai import types

            content = types.Content(role="user", parts=[types.Part(text=request_data)])
            final = None
            async for event in self.runner.run_async(
                session_id=context.task_id, user_id="backend_user", new_message=content,
            ):
                if event.is_final_response():
                    final = event
            if final and final.content and final.content.parts:
                text = _extract_text(final.content.parts)
                if text:
                    await updater.add_artifact([TextPart(text=text)], name="backend_report")
                    await updater.complete()
                    return
            await updater.update_status(TaskState.failed, message=new_agent_text_message("No backend report"), final=True)
        except Exception as e:
            logger.exception("Backend build failed")
            await updater.update_status(TaskState.failed, message=new_agent_text_message(f"Backend failed: {e}"), final=True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())