"""Tools del Docs Agent: scopes "docs" y "root" + lectura."""

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from src.tools.files import make_write_tool
from src.tools.files import read_file, list_tree


def get_tools() -> list:
    return [
        PreloadMemoryTool(),
        FunctionTool(func=make_write_tool("docs")),
        FunctionTool(func=make_write_tool("root")),
        FunctionTool(func=read_file),
        FunctionTool(func=list_tree),
    ]