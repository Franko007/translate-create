"""Tests offline de src/tools/mvp.py."""

from src.tools.files import write_file
from src.tools.mvp import SECRET_PATTERNS, check_mvp_checklist


def _build_compliant_project():
    write_file("LICENSE", "# Apache License, Version 2.0\n\nhttp://www.apache.org/licenses/LICENSE-2.0\n", scope="root")
    write_file(
        "README.md",
        "# Subtítulos Nerdearla\n\n## Requisitos\ninstalación con uv.\n"
        "## Como levantarlo\nlevantar el servidor, setup, inicio rapido.\n"
        "## Credenciales\nGEMINI_API_KEY o Vertex, ver .env.\n"
        "## Escalado\nescalar a mas sesiones con workers.\n"
        "## Como probar\ndemo con samples.\n",
        scope="root",
    )
    write_file(".env.example", "GEMINI_API_KEY=\nSPEECH_PROVIDER=mock\n", scope="root")
    write_file("samples/nerdearla.wav", "\x00\x01\x02", scope="root")
    write_file(
        "backend/server.py",
        "session_ids = [1, 2]\nfor session in session_ids:\n    pass\nsessions=2\n",
        scope="backend",
    )
    write_file("backend/exporter.py", "def export(ctx):\n    return 'srt'\n", scope="backend")


def test_mvp_pass_when_compliant():
    _build_compliant_project()
    result = check_mvp_checklist()
    assert result["passed"] is True
    assert result["passed_count"] == result["total"]
    assert result["checks"]["licencia_osi"]["ok"]
    assert result["checks"]["README_secciones"]["ok"]
    assert result["checks"]["env_example"]["ok"]
    assert result["checks"]["audios_prueba"]["ok"]
    assert result["checks"]["dos_sesiones"]["ok"]
    assert result["checks"]["export_srt_vtt"]["ok"]
    assert result["checks"]["sin_secretos"]["ok"]


def test_mvp_empty_sandbox_fails_all():
    result = check_mvp_checklist()
    assert result["passed"] is False
    assert result["passed_count"] == 0
    assert not result["checks"]["licencia_osi"]["ok"]


def test_mvp_detects_secret_leak():
    write_file("LICENSE", "# Apache License, Version 2.0\n", scope="root")
    write_file("backend/keys.txt", "AIzaSyDeadbeef0123456789abcdefghijklmnop", scope="backend")
    result = check_mvp_checklist()
    assert result["checks"]["sin_secretos"]["ok"] is False


def test_secret_patterns_cover_common_keys():
    assert SECRET_PATTERNS[0].search("AIzaSyA" + "x" * 30)
    assert not SECRET_PATTERNS[0].search("AIzaSyA" + "x" * 5)