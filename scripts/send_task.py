"""Cliente A2A (JSON-RPC) para disparar un build al planner en la nube.

Uso:
  uv run python scripts/send_task.py --url https://planner-xxxx-ues.a.run.app \
      --output build_report.json

Env alternativo: PLANNER_URL. Sin --url, apunta a http://127.0.0.1:8084.

Implementa las entradas A2A v0.2 (tasks/send + poll tasks/get) con httpx;
no depende del SDK del servidor.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx

from scripts.build_project import BUILD_ORDER

TERMINAL = {"completed", "failed", "canceled", "rejected", "input-required", "auth-required"}


def _post(base: str, client: httpx.Client, payload: dict) -> dict:
    for url in (f"{base.rstrip('/')}/", f"{base.rstrip('/')}/tasks"):
        try:
            r = client.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 405):
                continue
            raise
    raise RuntimeError(f"No se pudo alcanzar el endpoint JSON-RPC en {base}")


def _task_from(resp: dict) -> dict:
    result = resp.get("result", {})
    task = result.get("task")
    if task is not None:
        return task
    # algunos clientes devuelven un wrapper message/error; buscamos un task anidado
    inner = result.get("message")
    if isinstance(inner, dict) and "task" in inner:
        return inner["task"]
    raise RuntimeError(f"Respuesta A2A sin task: {resp}")


def _state(task: dict) -> str:
    status = task.get("status", {})
    return status.get("state", "unknown")


def _artifacts_text(task: dict) -> list[str]:
    texts = []
    for art in task.get("artifacts", []) or []:
        for part in art.get("parts", []) or []:
            if part.get("text"):
                texts.append(part["text"])
    return texts


def send(url: str, order: str, task_id: str, wait_s: int) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tasks/send",
        "params": {"id": task_id, "message": {"role": "user", "parts": [{"text": order}]}},
    }
    deadline = time.monotonic() + wait_s
    with httpx.Client(timeout=30) as client:
        print(f"send -> {url} (task {task_id})")
        resp = _post(url, client, payload)
        task = _task_from(resp)
        state = _state(task)

        while state not in TERMINAL:
            if time.monotonic() > deadline:
                raise TimeoutError(f"task {task_id} sigue en '{state}' tras {wait_s}s")
            time.sleep(5)
            resp = _post(
                url,
                client,
                {"jsonrpc": "2.0", "id": 1, "method": "tasks/get", "params": {"id": task_id}},
            )
            task = _task_from(resp)
            state = _state(task)
            print(f"  task {task_id}: {state}")

        texts = _artifacts_text(task)
        return {"state": state, "task": task, "artifacts_text": texts}


def main() -> int:
    ap = argparse.ArgumentParser(description="Dispara un build al planner agent (A2A)")
    ap.add_argument("--url", default=os.environ.get("PLANNER_URL", "http://127.0.0.1:8084"))
    ap.add_argument("--order", default=BUILD_ORDER, help="orden de build (default: la estandar)")
    ap.add_argument("--output", default=None, help="guardar el BuildReport (JSON) en este archivo")
    ap.add_argument("--wait-s", type=int, default=3600, help="tiempo maximo de espera (default 3600)")
    args = ap.parse_args()

    result = send(args.url, args.order, f"cli-{uuid.uuid4().hex[:12]}", args.wait_s)
    print(f"state: {result['state']}")
    report = result["artifacts_text"][-1] if result["artifacts_text"] else ""

    if args.output and report:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            out.write_text(json.dumps(json.loads(report), ensure_ascii=False, indent=2), encoding="utf-8")
        except json.JSONDecodeError:
            out.write_text(report, encoding="utf-8")
        print(f"BuildReport guardado en {out}")
    else:
        print(report or "(sin artefacto de texto)")

    return 0 if result["state"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())