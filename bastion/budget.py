"""
Micro-Budget Circuit Breaker.

Tracks cost and call count per session, and also enforces an account-wide
free tier cap across ALL sessions combined - so total usage stays within
the advertised free tier (e.g. 10,000 calls/month), resetting automatically.
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
        self._period_start = {}

        # Account-wide free tier tracking (across all sessions combined)
        self._total_calls = 0
        self._free_tier_period_start = time.monotonic()

    def _maybe_auto_reset(self, session_id: str) -> None:
        if self.config.reset_period_seconds is None:
            return
        now = time.monotonic()
        start = self._period_start.get(session_id)
        if start is None:
            self._period_start[session_id] = now
            return
        if now - start >= self.config.reset_period_seconds:
            self._spend[session_id] = 0.0
            self._calls[session_id] = 0
            self._period_start[session_id] = now

    def _maybe_reset_free_tier(self) -> None:
        now = time.monotonic()
        if now - self._free_tier_period_start >= self.config.free_tier_reset_period_seconds:
            self._total_calls = 0
            self._free_tier_period_start = now

    def check_before_call(self, session_id: str) -> None:
        self._maybe_auto_reset(session_id)

        # Account-wide free tier check (applies across ALL sessions combined)
        if self.config.free_tier_monthly_calls is not None:
            self._maybe_reset_free_tier()
            if self._total_calls >= self.config.free_tier_monthly_calls:
                raise BudgetExceeded(
                    f"Free tier limit reached: {self._total_calls} calls used "
                    f"out of {self.config.free_tier_monthly_calls} allowed this month, "
                    f"across all sessions combined."
                )

        # Per-session checks
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
        self._total_calls += 1
        return cost

    def get_session_stats(self, session_id: str) -> dict:
        return {
            "spend_usd": round(self._spend[session_id], 6),
            "calls": self._calls[session_id],
        }

    def get_free_tier_stats(self) -> dict:
        return {
            "total_calls_this_period": self._total_calls,
            "free_tier_limit": self.config.free_tier_monthly_calls,
        }

    def reset(self, session_id: str) -> None:
        self._spend.pop(session_id, None)
        self._calls.pop(session_id, None)
        self._period_start.pop(session_id, None)
