"""Deterministic tools for the builder agents (Nivel 1).

Todo lo que no debe decidir el LLM vive aca: el LLM decide y redacta, el codigo
ejecuta y mide. Todas las funcionalidades son import-standalone (stdlib) para
que la suite offline las pruebe sin ADK ni red.
"""

from .demo import run_demo
from .files import apply_patch, list_tree, make_write_tool
from .mvp import check_mvp_checklist
from .process import approve_stage, run_command
from .score import score_project

__all__ = [
    "run_demo",
    "apply_patch",
    "list_tree",
    "make_write_tool",
    "check_mvp_checklist",
    "approve_stage",
    "run_command",
    "score_project",
]