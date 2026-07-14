"""
Bastion test suite.

These tests use a fake embedding function so they run instantly, for free,
with no API key required. They verify the core detection logic works
correctly. (Bastion has also been separately verified against the live
OpenAI API - see example.py to run that yourself.)

Run with: pytest test_bastion.py -v
"""

import time
from bastion.config import BastionConfig
from bastion.loop_detector import LoopDetector
from bastion.retry_storm import RetryStormDetector
from bastion.budget import BudgetCircuitBreaker
from bastion.exceptions import LoopDetected, RetryStormDetected, BudgetExceeded


def fake_embed(text):
    """Deterministic fake embedding for offline testing - real embeddings are used in production."""
    core = " ".join(text.lower().split()[:3])
    return [float(ord(c)) for c in core.ljust(20)[:20]]


def test_loop_detector_flags_repeated_paraphrases():
    config = BastionConfig(loop_window_size=5, loop_similarity_threshold=0.99, loop_repeat_trigger=3)
    detector = LoopDetector(config, embed_fn=fake_embed)
    detector.check("s1", "What is the capital of France?")
    raised = False
    try:
        for _ in range(4):
            detector.check("s1", "What is the capital of France, exactly?")
    except LoopDetected:
        raised = True
    assert raised


def test_loop_detector_allows_varied_questions():
    config = BastionConfig(loop_window_size=5, loop_similarity_threshold=0.99, loop_repeat_trigger=3)
    detector = LoopDetector(config, embed_fn=fake_embed)
    detector.check("s2", "What is the capital of France?")
    detector.check("s2", "How tall is Mount Everest?")
    detector.check("s2", "Recommend a good pasta recipe.")


def test_retry_storm_detector_trips_on_burst():
    config = BastionConfig(retry_window_seconds=1.0, retry_max_calls=5, retry_cooldown_seconds=2.0)
    detector = RetryStormDetector(config)
    raised = False
    try:
        for _ in range(10):
            detector.check("s3")
    except RetryStormDetected:
        raised = True
    assert raised


def test_retry_storm_detector_allows_normal_pace():
    config = BastionConfig(retry_window_seconds=1.0, retry_max_calls=5, retry_cooldown_seconds=2.0)
    detector = RetryStormDetector(config)
    for _ in range(3):
        detector.check("s4")
        time.sleep(0.3)


def test_budget_breaker_blocks_over_cost_cap():
    config = BastionConfig(max_cost_usd_per_session=0.01, max_calls_per_session=1000)
    breaker = BudgetCircuitBreaker(config)
    breaker.check_before_call("s5")
    breaker.record_after_call("s5", model="gpt-4o", prompt_tokens=1000, completion_tokens=1000)
    raised = False
    try:
        breaker.check_before_call("s5")
    except BudgetExceeded:
        raised = True
    assert raised


def test_budget_breaker_blocks_over_call_count():
    config = BastionConfig(max_cost_usd_per_session=1000, max_calls_per_session=2)
    breaker = BudgetCircuitBreaker(config)
    breaker.check_before_call("s6")
    breaker.record_after_call("s6", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)
    breaker.check_before_call("s6")
    breaker.record_after_call("s6", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)
    raised = False
    try:
        breaker.check_before_call("s6")
    except BudgetExceeded:
        raised = True
    assert raised


def test_sessions_are_isolated():
    """Session A hitting its cap must never affect Session B's independent cap."""
    config_a = BastionConfig(max_calls_per_session=2)
    config_b = BastionConfig(max_calls_per_session=5)
    breaker_a = BudgetCircuitBreaker(config_a)
    breaker_b = BudgetCircuitBreaker(config_b)

    for _ in range(2):
        breaker_a.check_before_call("customer-A")
        breaker_a.record_after_call("customer-A", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)

    a_blocked = False
    try:
        breaker_a.check_before_call("customer-A")
    except BudgetExceeded:
        a_blocked = True
    assert a_blocked

    # Session B should be completely unaffected and succeed past A's cap
    for _ in range(5):
        breaker_b.check_before_call("customer-B")
        breaker_b.record_after_call("customer-B", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)


def test_budget_auto_reset():
    config = BastionConfig(max_calls_per_session=2, reset_period_seconds=1)
    breaker = BudgetCircuitBreaker(config)

    for _ in range(2):
        breaker.check_before_call("s7")
        breaker.record_after_call("s7", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)

    blocked = False
    try:
        breaker.check_before_call("s7")
    except BudgetExceeded:
        blocked = True
    assert blocked

    time.sleep(1.1)

    # Should work again automatically after the reset period, no manual reset needed
    breaker.check_before_call("s7")
