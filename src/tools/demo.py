"""Demo del producto generado, elevada a herramienta deterministica.

El contrato que fija ``architect_agent`` (spec/INTERFACES.md) exige que el
proyecto generado exponga un entrypoint ``demo/main.py --sessions N`` que:
  - levanta el pipeline con audio de ``samples/``,
  - emite N sesiones en paralelo,
  - imprime lineas ``METRIC <clave>=<valor>`` (latencia por etapa, errores).

Esta herramienta valida ese contrato y parsea las metricas; si falta el
entrypoint no ejecuta nada y devuelve un error deterministico.
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Any

from src.config import DEMO_ENTRY, RUN_TIMEOUT_S
from src.tools.files import list_tree
from src.tools.sandbox import sandbox_root, write_log

METRIC_RE = re.compile(r"^\s*METRIC\s+([A-Za-z_][\w]*)\s*=\s*([\w.:%+-]+)\s*$")


def _samples_ok(files: list[dict]) -> bool:
    return any("samples/" in f["path"] and f["path"].endswith((".wav", ".flac", ".mp3", ".ogg")) for f in files)


def run_demo(sessions: int = 2) -> dict[str, Any]:
    """Run the generated project's demo harness with N parallel sessions.

    Deterministic: validates the contract entry always exists before running
    anything. Returns parsed METRIC lines plus stdout/stderr tail.
    """
    root = sandbox_root()
    tree = list_tree()
    entry = root.joinpath(*DEMO_ENTRY.split("/"))
    if not entry.is_file():
        write_log("qa_agent", f"run_demo FAILED: missing contract entry {DEMO_ENTRY}")
        return {
            "ok": False,
            "error": f"El contrato exige {DEMO_ENTRY} en el proyecto generado (ver spec/INTERFACES.md). No se ejecuto nada.",
            "samples_ok": _samples_ok(tree.get("files", [])),
        }
    if not _samples_ok(tree.get("files", [])):
        write_log("qa_agent", "run_demo FAILED: no audio samples found")
        return {
            "ok": False,
            "error": "No hay audios de prueba en samples/ (*.wav|*.flac|*.mp3|*.ogg).",
            "samples_ok": False,
        }

    cmd = f"{sys.executable} -m demo.main --sessions {int(sessions)}"
    write_log("qa_agent", f"run_demo start: {cmd}")
    try:
        proc = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"demo timeout after {RUN_TIMEOUT_S}s", "sessions": int(sessions)}
    except OSError as e:
        return {"ok": False, "error": str(e), "sessions": int(sessions)}

    metrics: dict[str, Any] = {}
    for line in proc.stdout.splitlines():
        m = METRIC_RE.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            metrics[key] = value

    ok = proc.returncode == 0 and metrics.get("sessions_ok", 0) >= max(1, int(sessions))
    latencies = {k: v for k, v in metrics.items() if "latency" in k or k in ("t_audio_in", "t_emitted")}
    return {
        "ok": ok,
        "sessions": int(sessions),
        "returncode": proc.returncode,
        "metrics": metrics,
        "latency_by_stage": latencies,
        "errors": metrics.get("errors", 0),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-2000:],
        "samples_used": [f["path"] for f in tree.get("files", []) if "samples/" in f["path"]][:5],
        "contract": DEMO_ENTRY,
    }