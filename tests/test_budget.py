"""Tests offline de src/planner_agent/agent/budget.py (puro, sin deps)."""

from src.planner_agent.agent.budget import BudgetTracker


def test_iteration_budget():
    b = BudgetTracker(max_fix_iterations=3)
    assert b.start_iteration(1) is True
    assert b.start_iteration(3) is True
    assert b.start_iteration(4) is False
    assert b.iterations_used == 2


def test_token_budget():
    b = BudgetTracker(max_tokens_budget=1000)
    assert b.spend_tokens(600) is True
    assert b.tokens_spent == 600
    assert b.spend_tokens(600) is False
    assert b.tokens_remaining == 400


def test_snapshot_and_json():
    b = BudgetTracker()
    b.spend_tokens(100)
    snap = b.snapshot()
    assert snap["tokens_spent"] == 100
    assert "tokens_remaining" in snap
    assert "iterations_used" in b.to_json()
    assert b.approved is True