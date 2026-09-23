"""Tools del QA Agent: tests + demo + run_command + lectura."""

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from src.tools.demo import run_demo
from src.tools.files import make_write_tool
from src.tools.files import read_file, list_tree
from src.tools.process import run_command


def get_tools() -> list:
    return [
        PreloadMemoryTool(),
        FunctionTool(func=make_write_tool("tests")),
        FunctionTool(func=make_write_tool("demo")),
        FunctionTool(func=run_command),
        FunctionTool(func=run_demo),
        FunctionTool(func=read_file),
        FunctionTool(func=list_tree),
    ]