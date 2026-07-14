from sentinel import Sentinel, SentinelConfig, LoopDetected, RetryStormDetected, BudgetExceeded

config = SentinelConfig(retry_max_calls=5, retry_window_seconds=1.0, max_calls_per_session=50)
client = Sentinel(config=config)

session_id = "retry-test-1"

# Fire off a burst of DIFFERENT questions rapidly to trigger retry storm
# (not the loop detector, since these are all different topics)
questions = [
    "What is 2+2?", "What is the sky?", "What is water?",
    "What is fire?", "What is earth?", "What is wind?",
    "What is time?", "What is space?",
]

for i, q in enumerate(questions, start=1):
    print(f"\n--- Message {i}: {q}")
    try:
        response = client.chat.completions.create(
            session_id=session_id,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": q}],
        )
        print("Response:", response.choices[0].message.content[:60])
    except LoopDetected as e:
        print("BLOCKED - semantic loop:", e)
    except RetryStormDetected as e:
        print("BLOCKED - retry storm:", e)
    except BudgetExceeded as e:
        print("BLOCKED - budget exceeded:", e)
