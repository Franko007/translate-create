"""Tools del Reviewer Agent: solo lectura + checklist y score deterministicos."""

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from src.tools.files import read_file, list_tree
from src.tools.mvp import check_mvp_checklist
from src.tools.score import score_project


def get_tools() -> list:
    return [
        PreloadMemoryTool(),
        FunctionTool(func=check_mvp_checklist),
        FunctionTool(func=score_project),
        FunctionTool(func=read_file),
        FunctionTool(func=list_tree),
    ]