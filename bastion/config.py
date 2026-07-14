"""
Bastion configuration — tweak these to change sensitivity.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BastionConfig:
    # --- Semantic Loop Detector ---
    loop_window_size: int = 5
    loop_similarity_threshold: float = 0.75
    loop_repeat_trigger: int = 3

    # --- Retry Storm Detector ---
    retry_window_seconds: float = 1.0
    retry_max_calls: int = 10
    retry_cooldown_seconds: float = 5.0

    # --- Micro-Budget Circuit Breaker ---
    max_cost_usd_per_session: float = 2.00
    max_calls_per_session: int = 200

    # Optional auto-reset period for the budget breaker, in seconds.
    # e.g. 2592000 for a 30-day ("monthly") rolling reset.
    # None (default) = never auto-resets, matches original behavior —
    # a session stays blocked until reset_session() is called manually.
    reset_period_seconds: Optional[float] = None

    # --- Embeddings ---
    embedding_model: str = "text-embedding-3-small"
