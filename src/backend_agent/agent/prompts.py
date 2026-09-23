"""Prompts for the Backend Agent."""

import pathlib

_PROMPT_DIR = pathlib.Path(__file__).parent
INSTRUCTION = (_PROMPT_DIR / "instruction.md").read_text(encoding="utf-8")