import time
from bastion import Bastion, BastionConfig, BudgetExceeded

# Using 5 seconds here just so we can SEE it reset without waiting a month.
# In real use you'd set this to 2592000 (30 days) for a genuine monthly cap.
config = BastionConfig(max_calls_per_session=2, reset_period_seconds=5)
client = Bastion(config=config)

session_id = "monthly-test"

print("=== First period: use up the cap ===")
for i in range(1, 4):
    print(f"\n--- Call {i}")
    try:
        response = client.chat.completions.create(
            session_id=session_id,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED:", e)

print("\n\nWaiting 6 seconds for the period to reset...\n")
time.sleep(6)

print("=== New period: should work again automatically, no manual reset needed ===")
for i in range(1, 3):
    print(f"\n--- Call {i}")
    try:
        response = client.chat.completions.create(
            session_id=session_id,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED:", e)
