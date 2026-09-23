"""Control determinista de la corrida: iteraciones, tokens y log.

Separado del LLM para poder testearse offline. El planner consulta este objeto
antes de cada re-despliegue del bucle de correccion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class BudgetTracker:
    max_fix_iterations: int = 3
    max_tokens_budget: int = 200_000
    approved: bool = True
    tokens_spent: int = 0
    _iterations_used: list[int] = field(default_factory=list)

    def start_iteration(self, iteration: int) -> bool:
        """Return False if the fix-iteration budget is exhausted."""
        if iteration > self.max_fix_iterations:
            return False
        self._iterations_used.append(iteration)
        return True

    def spend_tokens(self, estimated: int) -> bool:
        """Charge estimated tokens; return False if the budget would be exceeded."""
        if self.tokens_spent + estimated > self.max_tokens_budget:
            return False
        self.tokens_spent += estimated
        return True

    @property
    def iterations_used(self) -> int:
        return len(self._iterations_used)

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.max_tokens_budget - self.tokens_spent)

    def snapshot(self) -> dict:
        return {
            "max_fix_iterations": self.max_fix_iterations,
            "iterations_used": self.iterations_used,
            "max_tokens_budget": self.max_tokens_budget,
            "tokens_spent": self.tokens_spent,
            "tokens_remaining": self.tokens_remaining,
            "approved": self.approved,
        }

    def to_json(self) -> str:
        return json.dumps(self.snapshot(), ensure_ascii=False)