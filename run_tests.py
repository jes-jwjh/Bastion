import sys, time
sys.path.insert(0, "_fake_deps")

from sentinel.config import SentinelConfig
from sentinel.loop_detector import LoopDetector
from sentinel.retry_storm import RetryStormDetector
from sentinel.budget import BudgetCircuitBreaker
from sentinel.exceptions import LoopDetected, RetryStormDetected, BudgetExceeded

passed = 0
failed = 0

def check(name, fn):
    global passed, failed
    try:
        fn()
        print(f"PASS: {name}")
        passed += 1
    except AssertionError as e:
        print(f"FAIL: {name} -> {e}")
        failed += 1
    except Exception as e:
        print(f"ERROR: {name} -> {type(e).__name__}: {e}")
        failed += 1

def fake_embed(text):
    core = " ".join(text.lower().split()[:3])
    return [float(ord(c)) for c in core.ljust(20)[:20]]

def test_loop_flags_repeats():
    config = SentinelConfig(loop_window_size=5, loop_similarity_threshold=0.99, loop_repeat_trigger=3)
    detector = LoopDetector(config, embed_fn=fake_embed)
    session = "s1"
    detector.check(session, "What is the capital of France?")
    raised = False
    try:
        for _ in range(4):
            detector.check(session, "What is the capital of France, exactly?")
    except LoopDetected:
        raised = True
    assert raised, "Expected LoopDetected to be raised"

def test_loop_allows_variety():
    config = SentinelConfig(loop_window_size=5, loop_similarity_threshold=0.99, loop_repeat_trigger=3)
    detector = LoopDetector(config, embed_fn=fake_embed)
    session = "s2"
    detector.check(session, "What is the capital of France?")
    detector.check(session, "How tall is Mount Everest?")
    detector.check(session, "Recommend a good pasta recipe.")

def test_retry_storm_trips():
    config = SentinelConfig(retry_window_seconds=1.0, retry_max_calls=5, retry_cooldown_seconds=2.0)
    detector = RetryStormDetector(config)
    session = "s3"
    raised = False
    try:
        for _ in range(10):
            detector.check(session)
    except RetryStormDetected:
        raised = True
    assert raised, "Expected RetryStormDetected to be raised"

def test_retry_storm_allows_normal_pace():
    config = SentinelConfig(retry_window_seconds=1.0, retry_max_calls=5, retry_cooldown_seconds=2.0)
    detector = RetryStormDetector(config)
    session = "s4"
    for _ in range(3):
        detector.check(session)
        time.sleep(0.3)

def test_budget_blocks_over_cost_cap():
    config = SentinelConfig(max_cost_usd_per_session=0.01, max_calls_per_session=1000)
    breaker = BudgetCircuitBreaker(config)
    session = "s5"
    breaker.check_before_call(session)
    breaker.record_after_call(session, model="gpt-4o", prompt_tokens=1000, completion_tokens=1000)
    raised = False
    try:
        breaker.check_before_call(session)
    except BudgetExceeded:
        raised = True
    assert raised, "Expected BudgetExceeded on cost cap"

def test_budget_blocks_over_call_count():
    config = SentinelConfig(max_cost_usd_per_session=1000, max_calls_per_session=2)
    breaker = BudgetCircuitBreaker(config)
    session = "s6"
    breaker.check_before_call(session)
    breaker.record_after_call(session, model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)
    breaker.check_before_call(session)
    breaker.record_after_call(session, model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)
    raised = False
    try:
        breaker.check_before_call(session)
    except BudgetExceeded:
        raised = True
    assert raised, "Expected BudgetExceeded on call-count cap"

check("loop detector flags repeated paraphrases", test_loop_flags_repeats)
check("loop detector allows varied questions", test_loop_allows_variety)
check("retry storm detector trips on burst", test_retry_storm_trips)
check("retry storm detector allows normal pace", test_retry_storm_allows_normal_pace)
check("budget breaker blocks over cost cap", test_budget_blocks_over_cost_cap)
check("budget breaker blocks over call count", test_budget_blocks_over_call_count)

print(f"\n{passed} passed, {failed} failed")
