from bastion import Bastion, BastionConfig, LoopDetected, RetryStormDetected, BudgetExceeded

config = BastionConfig(max_calls_per_session=2)
client = Bastion(config=config)

session_a = "customer-A"
session_b = "customer-B"

print("=== Session A: making calls until it hits its cap ===")
for i in range(1, 4):
    print(f"\n--- Session A, call {i}")
    try:
        response = client.chat.completions.create(
            session_id=session_a,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED - budget exceeded:", e)

print("\n\n=== Session B: should be completely unaffected by Session A ===")
for i in range(1, 3):
    print(f"\n--- Session B, call {i}")
    try:
        response = client.chat.completions.create(
            session_id=session_b,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED - budget exceeded:", e)

print("\n\nSession A stats:", client.get_session_stats(session_a))
print("Session B stats:", client.get_session_stats(session_b))
