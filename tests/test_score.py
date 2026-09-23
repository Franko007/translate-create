"""Tests offline de src/tools/score.py."""

from src.tools.files import write_file
from src.tools.score import CENTER_WEIGHTS, score_project


def _build_strong_project():
    write_file("LICENSE", "# Apache License, Version 2.0\n", scope="root")
    write_file(
        "README.md",
        "# Subtítulos\n\n## Requisitos\ninstalación.\n"
        "## Como levantarlo\nsetup.\n## Credenciales\nGEMINI_API_KEY, .env.\n"
        "## Escalado\nescalar sesiones con workers y redis.\n## Como probar\ndemo.\n",
        scope="root",
    )
    write_file(".env.example", "GEMINI_API_KEY=\n", scope="root")
    write_file("samples/a.wav", "abc", scope="root")
    write_file(
        "backend/server.py",
        "session_ids=[1,2]\nfor session in session_ids:\n    t_audio_in = 1.0\n    t_emitted = 1.5\nsessions=2\n",
        scope="backend",
    )
    write_file("backend/providers.py", "SPEECH_PROVIDER = 'mock'\nglosario = {'gpt': 'GPU tensor'}\n", scope="backend")
    write_file("backend/transcriber.py", "def transcribe(x):\n    return x\n", scope="backend")
    write_file("demo/main.py", "print('METRIC sessions_ok=2')\n", scope="root")
    write_file("tests/test_pipeline.py", "def test_x():\n    assert True\n", scope="root")
    write_file("docker-compose.yml", "services:\n  api:\n", scope="root")
    write_file("backend/exporter.py", "def export_srt(ctx):\n    return 'srt'\n", scope="backend")


def test_weights_sum_to_one():
    assert abs(sum(CENTER_WEIGHTS.values()) - 1.0) < 1e-9


def test_score_returns_structured_dims():
    _build_strong_project()
    result = score_project()
    assert result["method"] == "deterministic_score"
    assert set(result["dimensions"]) == set(CENTER_WEIGHTS)
    assert 0.0 <= result["overall_score"] <= 100.0
    assert result["mvp_component"] == 60.0
    assert result["extras"]["docker"] is True
    assert result["extras"]["demo_harness"] is True
    assert result["extras"]["tests_dir"] is True


def test_empty_project_scores_low():
    result = score_project()
    assert result["overall_score"] < 40
    assert result["verdict"] == "en_progreso"