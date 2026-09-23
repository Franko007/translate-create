"""Build runner del Nivel 1: seed del sandbox + corrida del planner.

Uso:
  uv run python scripts/build_project.py            # modo local (backend/frontend como AgentTool)
  BACKEND_AGENT_RESOURCE_NAME=... FRONTEND_AGENT_RESOURCE_NAME=... \\
      uv run python scripts/build_project.py        # via servicios A2A (Cloud Run/local)

Pasos:
  1. preflight (scripts/preflight.py).
  2. seed deterministico: copia spec/PRODUCT_BRIEF.md -> <out>/spec/ y la
     licencia Apache-2.0 de este repo -> <out>/LICENSE (el texto OSI completo
     NO lo escribe el LLM).
  3. corre el planner_agent (Runner/Runner) con la orden de construir.
  4. guarda <out>/.build_logs/build_report.md y el estado del presupuesto.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.preflight as preflight  # noqa: E402

from src.config import MAX_FIX_ITERATIONS, OUT_DIR  # noqa: E402
from src.planner_agent.agent.schemas import BuildReport  # noqa: E402
from src.tools.sandbox import sandbox_root, write_log  # noqa: E402

BUILD_ORDER = (
    "Construi el proyecto completo descrito en spec/PRODUCT_BRIEF.md dentro del sandbox "
    "(<out>/). Sali del requisito 6 del brief, respeta los scopes de escritura y usa "
    "el pipeline contract-first: architect -> backend + frontend -> qa/tests + demo -> "
    "reviewer -> docs. Toppa las iteraciones de correccion en "
    f"{MAX_FIX_ITERATIONS} y deja el informe final en espanol."
)


def seed_sandbox() -> None:
    """Copia los artefactos deterministicos del brief/licencia al sandbox."""
    root = sandbox_root()
    (root / "spec").mkdir(parents=True, exist_ok=True)
    brief_src = ROOT / "spec" / "PRODUCT_BRIEF.md"
    brief_dst = root / "spec" / "PRODUCT_BRIEF.md"
    if brief_src.exists() and (not brief_dst.exists() or brief_src.read_text(encoding="utf-8") != brief_dst.read_text(encoding="utf-8")):
        brief_dst.write_text(brief_src.read_text(encoding="utf-8"), encoding="utf-8")
        write_log("planner_agent", f"seed: spec/PRODUCT_BRIEF.md ({len(brief_src.read_text(encoding='utf-8'))} chars)")

    lic_src = ROOT / "LICENSE"
    lic_dst = root / "LICENSE"
    if lic_src.exists():
        if not lic_dst.exists():
            lic_dst.write_text(lic_src.read_text(encoding="utf-8"), encoding="utf-8")
            write_log("planner_agent", f"seed: LICENSE (apache-2.0, {len(lic_src.read_text(encoding='utf-8'))} chars)")


def run_planner() -> BuildReport:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService

    from src.planner_agent.agent import root_agent

    import asyncio
    from google.genai import types

    runner = Runner(
        app_name="planner_agent",
        agent=root_agent,
        session_service=InMemorySessionService(),
    )

    async def _core():
        final = None
        async for event in runner.run_async(
            session_id="build_project",
            user_id="build_cli",
            new_message=types.Content(role="user", parts=[types.Part(text=BUILD_ORDER)]),
        ):
            if event.is_final_response():
                final = event
        return final

    final = asyncio.run(_core())
    if not (final and final.content and final.content.parts):
        raise RuntimeError("El planner no genero informe final.")
    text = "".join(getattr(p, "text", "") or "" for p in final.content.parts)
    try:
        payload = json.loads(text[text.index("{"): text.rindex("}") + 1])
        return BuildReport.model_validate(payload)
    except Exception:
        raise RuntimeError("El informe final no es un BuildReport valido. Revisa .build_logs.")


def main() -> int:
    if preflight.main() != 0:
        return 1

    seed_sandbox()

    print(f"OUT_DIR: {OUT_DIR}")
    print("Corriendo planner_agent (agentes constructores)...")
    report = run_planner()

    log_dir = OUT_DIR / ".build_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_file = log_dir / "build_report.md"
    report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"BuildReport guardado en {report_file}")

    print("-" * 60)
    print(f"status: {report.status} | overall={report.scores.get('overall', 'n/a')}")
    print(f"iteraciones usadas: {report.iterations_used}/{MAX_FIX_ITERATIONS}")
    if report.blockers:
        print("blockers:")
        for b in report.blockers:
            print(f" - {b}")
    print("-" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())