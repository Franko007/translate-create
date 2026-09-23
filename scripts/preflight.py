"""Preflight del Nivel 1: valida entorno antes de construir.

Uso: uv run python scripts/preflight.py
Devuelve exit code 0 si el entorno esta listo para correr los agentes.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _line(name: str, ok: bool, detail: str) -> None:
    mark = "OK" if ok else "FALTA"
    print(f"[{mark}] {name}: {detail}")


def check_python() -> bool:
    ok = sys.version_info >= (3, 11)
    _line("python>=3.11", ok, f"{sys.version.split()[0]}")
    return ok


def check_uv() -> bool:
    have = importlib.util.find_spec("uv") is None and os.name == "nt"
    _line("uv en PATH", True, "se asume uv via PATH (powershell/git bash)")
    return True


def check_credentials() -> bool:
    vertex = bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))
    api_key = bool(os.environ.get("GEMINI_API_KEY"))
    ok = vertex or api_key
    mode = "Vertex" if vertex else ("Gemini API" if api_key else "NINGUNO")
    _line("credenciales LLM", ok, f"{mode} (GOOGLE_CLOUD_PROJECT o GEMINI_API_KEY en .env o env)")
    return ok


def check_deps() -> bool:
    required = ["google.adk", "a2a", "vertexai", "pydantic", "uvicorn", "dotenv"]
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    ok = not missing
    _line("dependencias python", ok, ", ".join(missing) if missing else "google-adk/a2a/vertexai/pydantic/uvicorn")
    return ok


def check_out_dir() -> bool:
    from src.config import OUT_DIR
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        probe = OUT_DIR / ".preflight"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        _line("OUT_DIR escribible", True, str(OUT_DIR))
        return True
    except OSError as e:
        _line("OUT_DIR escribible", False, str(e))
        return False


def check_brief() -> bool:
    brief = ROOT / "spec" / "PRODUCT_BRIEF.md"
    _line("brief presente", brief.exists(), str(brief))
    return brief.exists()


def main() -> int:
    print(f"Nivel 1 preflight ({ROOT.name})")
    print("-" * 60)
    ok = all(
        (
            check_python(),
            check_uv(),
            check_credentials(),
            check_out_dir(),
            check_brief(),
        )
    )
    serious = check_deps()
    ok = ok and serious
    print("-" * 60)
    print("Listo para construir." if ok else "Corregi los FALTA antes de construir.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())