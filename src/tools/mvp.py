"""Checklist MVP determinista del producto generado.

Escanea ``<out>`` y verifica los requisitos minimos de la vibeathon sin LLM:
licencia OSI, README con secciones obligatorias, .env.example, audios en
samples/, 2+ sesiones, exportador SRT/VTT, sin secretos hardcodeados.
"""

from __future__ import annotations

import re
from typing import Any

from src.tools.files import list_tree, read_file
from src.tools.sandbox import write_log

SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),              # Google API key
    re.compile(r"BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY"),  # private key
    re.compile(r"\bsk-[0-9A-Za-z]{20,}"),                # OpenAI-style
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                 # AWS access key
    re.compile(r"SERVICE_ACCOUNT\s*=.{8,}"),             # leak of a service account
)

README_SECTIONS = {
    "requisitos": ("Requisitos", "requisito", "instal"),
    "levantar": ("como levantarlo", "levantar", "setup", "instalacion", "inicio rapido"),
    "credenciales": ("credential", "credencial", "GEMINI_API_KEY", ".env"),
    "escalado": ("escal", "scal", "sesiones", "sessions"),
    "probar": ("probar", "test", "demo", "ejemplo"),
}


def _contains(haystack: str, needles) -> bool:
    low = haystack.lower()
    return any(n.lower() in low for n in needles)


def check_mvp_checklist() -> dict[str, Any]:
    """Deterministic MVP scan over the generated project."""
    tree = list_tree()
    files = [f["path"] for f in tree["files"]]
    text_by_path: dict[str, str] = {}
    for f in tree["files"]:
        try:
            text_by_path[f["path"]] = read_file(f["path"])["content"]
        except Exception:
            text_by_path[f["path"]] = ""
    all_text = "\n".join(text_by_path.values())

    checks: dict[str, dict[str, Any]] = {}

    lic = next((p for p in files if p.upper() == "LICENSE" or p.upper().endswith("/LICENSE")), None)
    license_ok = bool(lic and ("apache license, version 2.0" in all_text.lower() or "mit license" in all_text.lower()))
    checks["licencia_osi"] = {"ok": license_ok, "detail": f"LICENSE {'OK' if license_ok else 'faltante o sin texto OSI'} ({lic or 'no encontrado'})"}

    readme = next((p for p in files if p.lower() == "readme.md"), None)
    readme_text = text_by_path.get("README.md", "")
    missing_sections = [name for name, needles in README_SECTIONS.items() if not _contains(readme_text, needles)]
    checks["README_secciones"] = {
        "ok": readme is not None and not missing_sections,
        "detail": f"README {'OK' if readme and not missing_sections else 'faltan: ' + ', '.join(missing_sections or ['README']) }",
    }

    env_ok = any(p.lower() in (".env.example", ".env.example") or p.lower().endswith(".env.example") for p in files)
    checks["env_example"] = {"ok": env_ok, "detail": ".env.example presente" if env_ok else ".env.example faltante"}

    samples = [p for p in files if p.startswith("samples/") and p.lower().endswith((".wav", ".flac", ".mp3", ".ogg"))]
    checks["audios_prueba"] = {"ok": len(samples) >= 1, "detail": f"{len(samples)} audio(s) en samples/"}

    backend_text = "\n".join(v for k, v in text_by_path.items() if k.startswith("backend/") or k.startswith("pipeline/") or k.startswith("server/") or k.startswith("app/"))
    multi = any(s in backend_text.lower() for s in ("sessions=", "session_ids", "sessions=", "-sessions", "--sessions", "for session", "sesiones")) and (
        ">1" in backend_text or "2" in backend_text or "range(2" in backend_text or "enumerate(sessions" in backend_text
    )
    checks["dos_sesiones"] = {"ok": multi, "detail": "2+ sesiones en paralelo" if multi else "no se detecta manejo de 2+ sesiones"}

    export_ok = any("export" in p and p.endswith(".py") for p in files) and any(
        s in all_text.lower() for s in ("srt", "vtt")
    )
    checks["export_srt_vtt"] = {"ok": export_ok, "detail": "exportador SRT/VTT" if export_ok else "exportador SRT/VTT no detectado"}

    leaks = []
    for i, pat in enumerate(SECRET_PATTERNS):
        for path, content in text_by_path.items():
            for m in pat.finditer(content):
                leaked = content[max(0, m.start() - 30):m.end() + 10].replace("\n", " ").strip()[:80]
                if leaked not in [l_ for l_ in leaks]:
                    leaks.append(f"{path}: {leaked}")
                break
    checks["sin_secretos"] = {"ok": not leaks, "detail": "sin secretos hardcodeados OK" if not leaks else f"POSIBLES SECRETOS: {leaks[:3]}"}

    passed = sum(1 for c in checks.values() if c["ok"])
    total = len(checks)
    write_log("reviewer_agent", f"check_mvp_checklist: {passed}/{total} checks ok")
    return {
        "passed": passed == total,
        "passed_count": passed,
        "total": total,
        "checks": checks,
        "file_count": len(files),
        "method": "deterministic_mvp_scan",
    }