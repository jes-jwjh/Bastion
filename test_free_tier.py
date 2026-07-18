from bastion.config import BastionConfig
from bastion.budget import BudgetCircuitBreaker
from bastion.exceptions import BudgetExceeded

# Small free tier cap for a quick, fast test
config = BastionConfig(
    free_tier_monthly_calls=5,
    max_calls_per_session=1000,  # high so it doesn't interfere with this test
)
breaker = BudgetCircuitBreaker(config)

print("Testing account-wide free tier cap (limit = 5, across multiple sessions)...")

sessions = ["customer-A", "customer-B", "customer-C"]
call_count = 0

for i in range(7):
    session = sessions[i % len(sessions)]
    try:
        breaker.check_before_call(session)
        breaker.record_after_call(session, model="gpt-4o-mini", prompt_tokens=10, completion_tokens=10)
        call_count += 1
        print(f"Call {i+1} (session {session}): ALLOWED")
    except BudgetExceeded as e:
        print(f"Call {i+1} (session {session}): BLOCKED - {e}")

print(f"\nTotal successful calls: {call_count} (should be exactly 5)")
print("Free tier stats:", breaker.get_free_tier_stats())
