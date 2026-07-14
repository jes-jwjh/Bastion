"""
Micro-Budget Circuit Breaker.

Unlike provider-level monthly org caps (which nuke the whole account),
this tracks cost and call count per session/agent/user and kills only
that single session once it crosses its limit.

Optionally supports an auto-reset period (e.g. "monthly") so a session's
cap clears itself automatically without a developer needing to manually
call reset_session().
"""

import time
from collections import defaultdict

from .config import BastionConfig
from .exceptions import BudgetExceeded

MODEL_PRICE_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
}
DEFAULT_PRICE = {"input": 0.005, "output": 0.015}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = MODEL_PRICE_PER_1K_TOKENS.get(model, DEFAULT_PRICE)
    return (prompt_tokens / 1000) * price["input"] + (completion_tokens / 1000) * price["output"]


class BudgetCircuitBreaker:
    def __init__(self, config: BastionConfig):
        self.config = config
        self._spend = defaultdict(float)
        self._calls = defaultdict(int)
        # tracks when each session's current period started (for auto-reset)
        self._period_start = {}

    def _maybe_auto_reset(self, session_id: str) -> None:
        """If reset_period_seconds is set and the period has elapsed, clear this session automatically."""
        if self.config.reset_period_seconds is None:
            return

        now = time.monotonic()
        start = self._period_start.get(session_id)

        if start is None:
            # first time we've seen this session - start its period now
            self._period_start[session_id] = now
            return

        if now - start >= self.config.reset_period_seconds:
            self._spend[session_id] = 0.0
            self._calls[session_id] = 0
            self._period_start[session_id] = now

    def check_before_call(self, session_id: str) -> None:
        self._maybe_auto_reset(session_id)

        if self._spend[session_id] >= self.config.max_cost_usd_per_session:
            raise BudgetExceeded(
                f"Session '{session_id}' already spent "
                f"${self._spend[session_id]:.4f}, at or above the "
                f"${self.config.max_cost_usd_per_session:.2f} cap. Blocked."
            )
        if self._calls[session_id] >= self.config.max_calls_per_session:
            raise BudgetExceeded(
                f"Session '{session_id}' already made {self._calls[session_id]} "
                f"calls, at or above the {self.config.max_calls_per_session} cap. Blocked."
            )

    def record_after_call(self, session_id: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        cost = estimate_cost_usd(model, prompt_tokens, completion_tokens)
        self._spend[session_id] += cost
        self._calls[session_id] += 1
        return cost

    def get_session_stats(self, session_id: str) -> dict:
        return {
            "spend_usd": round(self._spend[session_id], 6),
            "calls": self._calls[session_id],
        }

    def reset(self, session_id: str) -> None:
        self._spend.pop(session_id, None)
        self._calls.pop(session_id, None)
        self._period_start.pop(session_id, None)
