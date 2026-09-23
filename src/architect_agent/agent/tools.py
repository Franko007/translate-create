"""Tools del Architect Agent: escritura en el scope "spec" + lectura."""

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from src.tools.files import make_write_tool


def get_tools() -> list:
    write_spec = make_write_tool("spec")

    read_file = __import__("src.tools.files", fromlist=["read_file"]).read_file
    list_tree = __import__("src.tools.files", fromlist=["list_tree"]).list_tree

    return [
        PreloadMemoryTool(),
        FunctionTool(func=write_spec),
        FunctionTool(func=read_file),
        FunctionTool(func=list_tree),
    ]