"""Tests offline de src/tools/demo.py (harness trivial real, sin red)."""

import sys

from src.tools.demo import METRIC_RE, run_demo
from src.tools.files import write_file


def test_metric_regex_parses_values():
    assert METRIC_RE.match("METRIC sessions_ok=2").group("key") == "sessions_ok"
    assert METRIC_RE.match("  METRIC latency_ttf_ms=812 ").group("value") == "812"


def test_run_demo_requires_contract_entry():
    res = run_demo(sessions=2)
    assert res["ok"] is False
    assert "demo/main.py" in res["error"]


def test_run_demo_runs_harness_and_parses_metrics():
    write_file(
        "demo/main.py",
        "import sys\n"
        "sessions = 2\n"
        "print('METRIC sessions_ok=%d' % sessions)\n"
        "print('METRIC errors=0')\n"
        "print('METRIC latency_ttf_ms=812')\n",
        scope="root",
    )
    write_file("samples/nerdearla.wav", "audio-bytes", scope="root")
    res = run_demo(sessions=2)
    assert res["ok"] is True
    assert res["metrics"]["sessions_ok"] == 2
    assert res["metrics"]["errors"] == 0
    assert res["latency_by_stage"]["latency_ttf_ms"] == 812
    assert res["sessions"] == 2