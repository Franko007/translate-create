"""Tests offline de src/tools/files.py."""

import pytest

from src.tools.files import (
    append_file,
    apply_patch,
    check_patch,
    list_tree,
    make_write_tool,
    read_file,
    write_file,
)


def test_write_then_read_roundtrip():
    res = write_file("README.md", "# Hola\n", scope="root")
    assert res["ok"] and res["action"] == "written"
    data = read_file("README.md")
    assert data["content"] == "# Hola\n"
    assert data["path"] == "README.md"


def test_write_nested_creates_parents():
    write_file("backend/server/app.py", "print(1)", scope="backend")
    assert (read_file("backend/server/app.py"))["content"] == "print(1)"


def test_append_and_append_requires_existing():
    write_file("server.py", "a=1", scope="backend")
    append_file("server.py", "\nb=2", scope="backend")
    assert read_file("backend/server.py")["content"] == "a=1\nb=2"
    with pytest.raises(ValueError, match="existing"):
        append_file("ghost.py", "x", scope="backend")


def test_read_missing_raises():
    with pytest.raises(ValueError, match="not found"):
        read_file("nope.md")


def test_list_tree_lists_content():
    write_file("a.txt", "aa", scope="root")
    write_file("backend/b.py", "bb", scope="backend")
    write_file("spec/c.json", "{}", scope="spec")
    tree = list_tree()
    paths = [f["path"] for f in tree["files"]]
    assert "a.txt" in paths
    assert "backend/b.py" in paths
    assert "spec/c.json" in paths
    assert tree["file_count"] == 3


def test_apply_patch_ops():
    write_file("app.py", "alpha\nbeta\nalpha\n", scope="root")
    apply_patch(
        "app.py",
        [
            {"op": "replace", "old": "beta", "new": "BETA"},
            {"op": "replace_all", "old": "alpha", "new": "ALFA"},
            {"op": "insert_after", "anchor": "BETA", "new": "\ngamma"},
            {"op": "delete", "old": "\nalpha"},
        ],
        scope="root",
    )
    assert read_file("app.py")["content"] == "ALFA\nBETA\ngamma\n"


def test_apply_patch_missing_anchor_raises():
    write_file("x.txt", "hola", scope="root")
    with pytest.raises(ValueError, match="anchor not found"):
        apply_patch("x.txt", [{"op": "replace", "old": "zz", "new": "y"}], scope="root")


def test_check_patch_validation():
    assert check_patch('[{"op":"replace","old":"a","new":"b"}]')["ok"]
    assert not check_patch('{"a":1}')["ok"]
    assert not check_patch('[{"op":"wat","old":"a"}]')["ok"]


def test_make_write_tool_locks_scope():
    tool = make_write_tool("docs")
    res = tool("GOTCHAS.md", "trampa\n")
    assert res["path"] == "docs/GOTCHAS.md"