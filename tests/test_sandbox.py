"""Tests offline de src/tools/sandbox.py."""

import pytest

from src.tools.sandbox import SCOPES, resolve_read, resolve_write, sandbox_root, write_log


def test_scopes_registry():
    assert set(SCOPES) == {"spec", "backend", "frontend", "tests", "demo", "docs", "meta", "root"}


def test_resolve_write_creates_and_maps():
    target = resolve_write("spec", "ARCHITECTURE.md")
    assert target.name == "ARCHITECTURE.md"
    assert "spec" in target.parts
    assert str(target).startswith(str(sandbox_root()))


def test_resolve_write_root_is_sandbox_root():
    assert resolve_write("root", "README.md").parent == sandbox_root()


@pytest.mark.parametrize(
    "rel",
    [
        "../etc/passwd",
        "..",
        "backend/../../secret",
        "C:\\Windows\\system32\\calc.exe",
        "/etc/passwd",
    ],
)
def test_resolve_write_rejects_escapes(rel):
    for scope in ("spec", "backend", "root"):
        with pytest.raises(ValueError, match="escape"):
            resolve_write(scope, rel)


def test_resolve_write_unknown_scope():
    with pytest.raises(ValueError, match="unknown sandbox scope"):
        resolve_write("nope", "x.txt")


def test_resolve_read_internal_and_reject_escape():
    assert resolve_read("spec/INTERFACES.md").name == "INTERFACES.md"
    with pytest.raises(ValueError, match="escape"):
        resolve_read("../outside")


def test_write_log_appends_run_log():
    write_log("planner_agent", "hola test")
    log = sandbox_root() / ".build_logs" / "run.log"
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "planner_agent" in text and "hola test" in text