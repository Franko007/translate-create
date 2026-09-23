"""Tests offline de src/tools/process.py (sin ejecutar subprocesos)."""

from src.tools.process import ALLOWED_PREFIXES, BANNED_MARKERS, approve_stage, run_command, _validate


def test_validate_allows_whitelisted():
    for allowed in ("uv sync", "uv run pytest", "python samples/check.py", "ls -la"):
        assert _validate(allowed) is None


def test_validate_rejects_unknown():
    assert _validate("echo hi") is not None
    assert _validate("pip install requests") is not None
    assert _validate("") is not None


def test_validate_rejects_banned_even_if_prefixed():
    assert _validate("ls -la; rm -rf /") is not None
    assert "banned" in _validate("git push origin main")


def test_banned_and_allowed_are_consistent():
    for b in BANNED_MARKERS:
        assert b not in " ".join(ALLOWED_PREFIXES)


def test_approve_stage_modes():
    assert approve_stage("x")["approved"] is False  # APPROVAL_MODE=ask del conftest
    assert approve_stage("x")["mode"] == "ask"
    assert "HUMAN_APPROVAL" in approve_stage("x")["message"]


def test_run_command_rejects_outside_whitelist_without_exec():
    res = run_command("curl https://evil.example")
    assert res["ok"] is False
    assert res.get("rejected") is True
    res2 = run_command("rm -rf /tmp/whatever")
    assert res2.get("rejected") is True


def test_run_command_ask_returns_approval_gate():
    res = run_command("uv run pytest")
    assert res["ok"] is False
    assert res.get("approved") is False
    assert "HUMAN_APPROVAL" in res.get("message", "")