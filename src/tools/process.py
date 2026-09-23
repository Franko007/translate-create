"""Ejecucion de comandos controlada (whitelist + timeout + puertas humanas).

El LLM nunca ejecuta codigo directo; solo via esta herramienta, que limita los
comandos a una lista blanca, corre dentro del sandbox y respeta
``APPROVAL_MODE`` (yes | no | ask) sin bloquear el agente.
"""

from __future__ import annotations

import subprocess
from typing import Any

from src.config import APPROVAL_MODE, RUN_TIMEOUT_S
from src.tools.sandbox import sandbox_root, write_log

ALLOWED_PREFIXES = (
    "uv sync",
    "uv run pytest",
    "uv run ruff",
    "uv run python -m pytest",
    "ruff check",
    "python -m pytest",
    "python -m demo.main",
    "python -m app",
    "python -m server.app",
    "python -m server.demo",
    "python samples/",
    "python scripts/",
    "pwd",
    "ls -la",
    "find . -maxdepth 3",
)

BANNED_MARKERS = (
    "rm -rf",
    "rm -fr",
    "sudo",
    "git push",
    "curl ",
    "wget ",
    "> /",
    "&& rm",
    "mkfs",
    "dd if=",
)


def _validate(cmd: str) -> str | None:
    if not cmd or not cmd.strip():
        return "empty command"
    if any(b in cmd for b in BANNED_MARKERS):
        return f"banned marker in command: {cmd}"
    if not any(cmd.strip().startswith(p) for p in ALLOWED_PREFIXES):
        allowed = " | ".join(ALLOWED_PREFIXES)
        return f"command not in whitelist (allow: {allowed}): {cmd}"
    return None


def approve_stage(action: str) -> dict[str, Any]:
    """Puerta de aprobacion humana para comandos sensibles (no bloquea al agente)."""
    if APPROVAL_MODE == "yes":
        return {"approved": True, "mode": "yes"}
    if APPROVAL_MODE == "no":
        return {"approved": False, "mode": "no", "message": f"APPROVAL_MODE=no, stage skipped: {action}"}
    # ask: devuelve el pedido como reves; el humano lo aprueba y re-corre.
    return {
        "approved": False,
        "mode": "ask",
        "message": f"HUMAN_APPROVAL REQUIRED: {action}. Set APPROVAL_MODE=yes for headless runs.",
    }


def run_command(cmd: str, timeout_s: int = 0) -> dict[str, Any]:
    """Run a whitelisted command inside the sandbox and capture stdout/stderr."""
    error = _validate(cmd)
    if error:
        write_log("qa_agent", f"run_command REJECTED: {cmd} ({error})")
        return {"ok": False, "rejected": True, "reason": error}

    if APPROVAL_MODE == "ask":
        decision = approve_stage(f"run command: {cmd}")
        if not decision["approved"]:
            return {"ok": False, "approved": False, "message": decision["message"]}

    timeout = timeout_s or RUN_TIMEOUT_S
    root = sandbox_root()
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout,
        )
        write_log("qa_agent", f"run_command ok ({proc.returncode}): {cmd}")
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-4000:],
            "cwd": str(root),
        }
    except subprocess.TimeoutExpired:
        write_log("qa_agent", f"run_command TIMEOUT after {timeout}s: {cmd}")
        return {"ok": False, "error": f"timeout after {timeout}s", "cwd": str(root)}
    except OSError as e:
        return {"ok": False, "error": str(e), "cwd": str(root)}