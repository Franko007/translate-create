"""Scoring deterministico del producto generado (componente del reviewer).

Combina el checklist MVP con senales objetivas del codigo (docker, medicion de
latencia por etapa, contrato de demo, hot path sin orquestador LLM). El
``reviewer_agent`` (LLM) toma estos numeros y agrega el juicio narrativo contra
los criterios del jurado.
"""

from __future__ import annotations

import re
from typing import Any

from src.tools.files import list_tree, read_file
from src.tools.mvp import check_mvp_checklist

CENTER_WEIGHTS = {
    "calidad": 0.25,
    "latencia": 0.20,
    "escalabilidad": 0.20,
    "despliegue": 0.15,
    "innovacion": 0.20,
}


def score_project() -> dict[str, Any]:
    """Compute a deterministic score (0-100) over the generated project."""
    mvp = check_mvp_checklist()
    tree = list_tree()
    files = [f["path"] for f in tree["files"]]
    text_by_path = {
        f["path"]: read_file(f["path"])["content"]
        for f in tree["files"]
        if not f["path"].endswith((".png", ".jpg", ".wav", ".flac", ".mp3"))
    }
    all_text = "\n".join(text_by_path.values()).lower()

    mvp_ratio = mvp["passed_count"] / max(1, mvp["total"])
    mvp_score = round(mvp_ratio * 60.0, 1)  # 60 puntos disponibles

    extras = _objective_extras(files, all_text)

    # Escala logica determinista 0-40 (al MvP se le suman los extras)
    dims: dict[str, dict[str, Any]] = {
        "calidad": {"ok": bool(re.search(r"glosario|glossary", all_text)) or "providers.py" in "\n".join(text_by_path), "note": "STT + glosario / proveedores encontrados"},
        "latencia": {"ok": bool(re.search(r"(t_audio_in|t_emitted|latency|latenc)", all_text)), "note": "medicion de latencia por etapa"},
        "escalabilidad": {"ok": bool(re.search(r"(sesion|session|worker|concurrent|hilos|threads)", all_text)) and bool(re.search(r"(scale|escal|redis|pub.?sub)", all_text)), "note": "sesiones + escalado/redis"},
        "despliegue": {"ok": "docker-compose.yml" in "\n".join(text_by_path) or "dockerfile" in "\n".join(text_by_path), "note": "docker compose / Dockerfile"},
        "innovacion": {"ok": bool(re.search(r"(srt|vtt|obs|api.?key|vertex)", all_text)), "note": "extras: export, OBS, multi-provider"},
    }
    dim_scores = {k: (20, v["note"]) if v["ok"] else (0, v["note"]) for k, v in dims.items()}
    extras_total = round(sum(score for score, _ in dim_scores.values()) * (mvp_ratio * 0.5 + 0.5), 1)
    extras_total = min(extras_total, 40.0)

    total = round(min(100.0, mvp_score + extras_total), 1)

    return {
        "overall_score": total,
        "mvp_component": mvp_score,
        "extras_component": extras_total,
        "dimensions": {k: {"score": s[0], "note": s[1]} for k, s in dim_scores.items()},
        "mvp": mvp,
        "extras": extras,
        "verdict": "aprobado" if total >= 85 else "en_progreso",
        "method": "deterministic_score",
    }


def _objective_extras(files: list[str], all_text: str) -> dict[str, bool]:
    return {
        "docker": any(f.lower() in ("docker-compose.yml", "docker-compose.yaml") or f.lower().endswith("/docker-compose.yml") for f in files)
        or any("dockerfile" in f.lower() for f in files),
        "demo_harness": any(f == "demo/main.py" for f in files),
        "tests_dir": any(f.startswith("tests/") and f.endswith(".py") for f in files),
        "hot_path_no_llm": "api" in all_text or "websocket" in all_text,
    }