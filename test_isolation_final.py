from bastion import Bastion, BastionConfig, BudgetExceeded

# Session A gets a LOW cap (2 calls), Session B gets a HIGHER cap (5 calls)
# If isolation is broken, B would incorrectly get blocked around call 2-3 (matching A's cap)
# If isolation works, B should sail all the way to 5 calls with zero issue

config = BastionConfig(max_calls_per_session=100)  # generous default, we override per-test below
client = Bastion(config=config)

# Manually set different caps per session by using two separate configs/clients instead
config_a = BastionConfig(max_calls_per_session=2)
config_b = BastionConfig(max_calls_per_session=5)

client_a = Bastion(config=config_a)
client_b = Bastion(config=config_b)

print("=== SESSION A (cap = 2) ===")
for i in range(1, 5):
    print(f"\n--- Session A, call {i}")
    try:
        response = client_a.chat.completions.create(
            session_id="customer-A",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED:", e)

print("\n\n=== SESSION B (cap = 5) - should succeed well past where A got blocked ===")
for i in range(1, 6):
    print(f"\n--- Session B, call {i}")
    try:
        response = client_b.chat.completions.create(
            session_id="customer-B",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello, message {i}"}],
        )
        print("Response:", response.choices[0].message.content)
    except BudgetExceeded as e:
        print("BLOCKED:", e)

print("\n\nSession A stats:", client_a.get_session_stats("customer-A"))
print("Session B stats:", client_b.get_session_stats("customer-B"))
