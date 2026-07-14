import time
from bastion import Bastion, BastionConfig, LoopDetected, RetryStormDetected, BudgetExceeded

config = BastionConfig(max_calls_per_session=2, reset_period_seconds=5)
client = Bastion(config=config)

session_id = "monthly-test-2"

# Using genuinely different questions this time so we don't accidentally
# trip the (separate) loop detector while testing the budget reset.
questions_period_1 = ["What is the capital of Japan?", "How tall is Mount Everest?", "What is DNA made of?"]
questions_period_2 = ["Recommend a good pizza topping.", "What language is spoken in Brazil?"]

def run_calls(questions, label):
    for i, q in enumerate(questions, start=1):
        print(f"\n--- {label}, call {i}: {q}")
        try:
            response = client.chat.completions.create(
                session_id=session_id,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": q}],
            )
            print("Response:", response.choices[0].message.content[:60])
        except LoopDetected as e:
            print("BLOCKED - loop:", e)
        except RetryStormDetected as e:
            print("BLOCKED - retry storm:", e)
        except BudgetExceeded as e:
            print("BLOCKED - budget:", e)

print("=== First period: use up the cap ===")
run_calls(questions_period_1, "Period 1")

print("\n\nWaiting 6 seconds for the period to reset...\n")
time.sleep(6)

print("=== New period: should work again automatically ===")
run_calls(questions_period_2, "Period 2")
