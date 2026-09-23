"""Sandbox del proyecto generado.

Todo archivo que generan los agentes vive dentro de ``OUT_DIR``. Los scopes
mapean a subcarpetas con responsabilidad unica; ``root`` es la raiz del
proyecto generado. Rutas absolutas, ``..`` y enlaces simbolicos que escapen del
sandbox se rechazan.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from src.config import OUT_DIR

# scope -> subcarpeta ("" es la raiz del proyecto generado)
SCOPES = {
    "spec": "spec",
    "backend": "backend",
    "frontend": "frontend",
    "tests": "tests",
    "demo": "demo",
    "docs": "docs",
    "meta": ".build_logs",
    "root": "",
}


def sandbox_root() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR.resolve()


def _scope_dir(scope: str) -> Path:
    if scope not in SCOPES:
        raise ValueError(f"unknown sandbox scope: {scope}")
    return (sandbox_root() / SCOPES[scope]).resolve()


def resolve_write(scope: str, rel: str) -> Path:
    """Resolve a write target under a scope, rejecting escapes."""
    if scope not in SCOPES:
        raise ValueError(f"write must target a sandbox scope, got: {scope}")
    base = _scope_dir(scope)
    target = Path(rel)
    if target.is_absolute() or ".." in target.parts:
        raise ValueError(f"escape attempt rejected: {rel}")
    resolved = (base / target).resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"escape attempt rejected: {rel}")
    return resolved


def resolve_read(rel: str) -> Path:
    """Resolve a read target anywhere inside the sandbox (read-only)."""
    root = sandbox_root()
    target = Path(rel)
    absolute = target if target.is_absolute() else root / target
    resolved = absolute.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"escape attempt rejected: {rel}")
    return resolved


def write_log(agent: str, message: str) -> None:
    """Append one action to ``<out>/.build_logs/run.log`` (log reproducible)."""
    from src.tools.files import append_sandbox_file

    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {agent}: {message}"
    append_sandbox_file(str(Path(".build_logs") / "run.log"), line + os.linesep)