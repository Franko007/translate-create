"""A2A Agent Executor for the Planner Agent."""

import logging
import os

import vertexai
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger(__name__)


def _extract_text(parts) -> str:
    """Get text from response parts (text or final_response function call args)."""
    chunks = []
    for p in parts or []:
        if hasattr(p, "text") and p.text:
            chunks.append(p.text)
        elif hasattr(p, "function_call") and p.function_call and p.function_call.args:
            args = p.function_call.args
            if isinstance(args, dict):
                chunks.append(json.dumps(args, ensure_ascii=False))
            else:
                chunks.append(str(args))
    return "".join(chunks)


class PlannerExecutor(AgentExecutor):
    """Execute build requests over A2A, one complete run per request."""

    def __init__(self):
        self.agent = None
        self.runner = None

    def _init_agent(self) -> None:
        if self.agent is None:
            from ..agent import root_agent

            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
            if project_id:
                vertexai.init(project=project_id, location=location)
            self.agent = root_agent

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
            await updater.update_status(TaskState.failed, message=new_agent_text_message("No request data"), final=True)
            return

        try:
            await updater.update_status(TaskState.working, message=new_agent_text_message("Construyendo el proyecto (agentes activos)..."))

            content = types.Content(role="user", parts=[types.Part(text=request_data)])
            final_event = None
            async for event in self.runner.run_async(
                session_id=context.task_id, user_id="planner_user", new_message=content,
            ):
                if event.is_final_response():
                    final_event = event

            if final_event and final_event.content and final_event.content.parts:
                text = _extract_text(final_event.content.parts)
                if text:
                    await updater.add_artifact([TextPart(text=text)], name="build_report")
                    await updater.complete()
                    return

            await updater.update_status(TaskState.failed, message=new_agent_text_message("No se genero informe final"), final=True)
        except Exception as e:
            logger.exception("Build failed")
            await updater.update_status(TaskState.failed, message=new_agent_text_message(f"Build failed: {e}"), final=True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())