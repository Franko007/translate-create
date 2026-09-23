"""Herramientas deterministicas de archivos (sandboxeada).

- ``write_file`` / ``append_file``: escriben dentro de un scope.
- ``read_file`` / ``list_tree``: lectura en cualquier parte del sandbox.
- ``apply_patch``: operaciones en archivos ya escritos.
- ``make_write_tool(scope)``: fabrica la funcion con scope fijo que expone el
  agente como tool (el scope queda encerrado, no lo decida el LLM).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from src.tools.sandbox import resolve_read, resolve_write, sandbox_root, write_log


def write_file(path: str, content: str, scope: str) -> dict[str, Any]:
    """Create or overwrite a file inside the given sandbox scope."""
    target = resolve_write(scope, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    write_log(scope, f"wrote {target.relative_to(sandbox_root())} ({len(content)} chars)")
    return {
        "ok": True,
        "path": str(target.relative_to(sandbox_root())),
        "bytes": len(content.encode("utf-8")),
        "action": "written",
    }


def append_sandbox_file(path: str, content: str) -> dict[str, Any]:
    """Append to a file anywhere inside the sandbox (usado por el build log)."""
    target = resolve_write("root", path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(content)
    return {"ok": True, "path": str(target.relative_to(sandbox_root())), "action": "appended"}


def append_file(path: str, content: str, scope: str) -> dict[str, Any]:
    """Append content to an existing file inside the sandbox."""
    target = resolve_write(scope, path)
    if not target.exists():
        raise ValueError(f"append_file requires an existing file: {path}")
    with target.open("a", encoding="utf-8") as fh:
        fh.write(content)
    write_log(scope, f"appended {target.relative_to(sandbox_root())}")
    return {"ok": True, "path": str(target.relative_to(sandbox_root())), "action": "appended"}


def read_file(path: str) -> dict[str, Any]:
    """Read back any sandboxed file (read-only)."""
    target = resolve_read(path)
    if not target.exists():
        raise ValueError(f"read_file: file not found in sandbox: {path}")
    text = target.read_text(encoding="utf-8")
    return {
        "ok": True,
        "path": str(target.relative_to(sandbox_root())),
        "lines": len(text.splitlines()),
        "content": text,
    }


def list_tree(path: str = "") -> dict[str, Any]:
    """List the sandbox tree (with sizes), read-only."""
    base = resolve_read(path) if path else sandbox_root()
    if base.is_file():
        base = base.parent
    files = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or ".git" in p.parts or ".build_logs" in p.parts:
            continue
        rel = p.relative_to(sandbox_root())
        files.append({"path": str(rel).replace("\\", "/"), "bytes": p.stat().st_size})
    return {"ok": True, "root": str(sandbox_root()), "file_count": len(files), "files": files}


def apply_patch(path: str, operations: list[dict], scope: str) -> dict[str, Any]:
    """Apply deterministic text operations to a sandboxed file.

    ``operations`` is a JSON list of:
      {"op": "replace", "old": str, "new": str}   (first occurrence)
      {"op": "replace_all", "old": str, "new": str}
      {"op": "delete", "old": str}                (first occurrence)
      {"op": "insert_after", "anchor": str, "new": str}
    """
    target = resolve_write(scope, path)
    if not target.exists():
        raise ValueError(f"apply_patch requires an existing file: {path}")
    text = target.read_text(encoding="utf-8")

    for op in operations or []:
        kind = op.get("op")
        if kind == "replace":
            old, new = op["old"], op["new"]
            if old not in text:
                raise ValueError(f"patch anchor not found: {op['old'][:60]}")
            text = text.replace(old, new, 1)
        elif kind == "replace_all":
            if op["old"] not in text:
                raise ValueError(f"patch anchor not found: {op['old'][:60]}")
            text = text.replace(op["old"], op["new"])
        elif kind == "delete":
            if op["old"] not in text:
                raise ValueError(f"patch anchor not found: {op['old'][:60]}")
            text = text.replace(op["old"], "", 1)
        elif kind == "insert_after":
            if op["anchor"] not in text:
                raise ValueError(f"patch anchor not found: {op['anchor'][:60]}")
            text = text.replace(op["anchor"], op["anchor"] + op["new"], 1)
        else:
            raise ValueError(f"unknown patch op: {kind}")

    target.write_text(text, encoding="utf-8")
    write_log(scope, f"patched {target.relative_to(sandbox_root())}")
    return {"ok": True, "path": str(target.relative_to(sandbox_root())), "action": "patched"}


def check_patch(operations: str) -> dict[str, Any]:
    """Validate a patch payload without touching the filesystem (deterministic)."""
    try:
        ops = json.loads(operations)
        if not isinstance(ops, list):
            raise ValueError("operations must be a JSON list")
        for op in ops:
            if op.get("op") not in {"replace", "replace_all", "delete", "insert_after"}:
                raise ValueError(f"unknown op: {op.get('op')}")
            if "old" not in op and op.get("op") != "insert_after":
                raise ValueError("missing 'old'")
        return {"ok": True, "operations": len(ops)}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"invalid JSON: {e}"}


def _bind(scope: str, fn: Callable[..., dict]) -> Callable[..., dict]:
    """Bind a scope so the exposed tool signature stays ``(path, ...)``."""

    def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["scope"] = scope
        return fn(*args, **kwargs)

    wrapped.__name__ = fn.__name__
    wrapped.__doc__ = fn.__doc__
    return wrapped


def make_write_tool(scope: str) -> Callable[[str, str], dict[str, Any]]:
    """Expose ``write_file(path, content)`` locked to ``scope``.

    El LLM de cada agente recibe esta funcion con el scope ya fijado al crear la
    herramienta; nunca puede elegir a donde escribir.
    """
    return _bind(scope, write_file)


def make_patch_tool(scope: str) -> Callable[[str, list], dict[str, Any]]:
    return _bind(scope, apply_patch)


def make_append_tool(scope: str) -> Callable[[str, str], dict[str, Any]]:
    return _bind(scope, append_file)