"""
Bastion configuration - tweak these to change sensitivity.
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

    # --- Micro-Budget Circuit Breaker (per session) ---
    max_cost_usd_per_session: float = 2.00
    max_calls_per_session: int = 200
    reset_period_seconds: Optional[float] = None

    # --- Account-wide Free Tier Cap (across ALL sessions combined) ---
    # Set to None to disable this cap entirely.
    free_tier_monthly_calls: Optional[int] = 10000
    free_tier_reset_period_seconds: float = 2592000  # 30 days

    # --- Embeddings ---
    embedding_model: str = "text-embedding-3-small"
