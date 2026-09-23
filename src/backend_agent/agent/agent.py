"""Backend Agent - LlmAgent wiring."""

import os

import vertexai
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig, ThinkingConfig

from .config import AGENT_DESCRIPTION, AGENT_NAME, MODEL
from .prompts import INSTRUCTION
from .schemas import BackendReport
from .tools import get_tools

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
if project_id:
    vertexai.init(project=project_id, location=location)

root_agent = LlmAgent(
    name=AGENT_NAME,
    model=MODEL,
    description=AGENT_DESCRIPTION,
    static_instruction=INSTRUCTION,
    output_schema=BackendReport,
    tools=get_tools(),
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=512),
        max_output_tokens=2048,
    ),
)

__all__ = ["AGENT_NAME", "AGENT_DESCRIPTION", "MODEL", "root_agent"]