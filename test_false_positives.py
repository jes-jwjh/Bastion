from sentinel import Sentinel, SentinelConfig, LoopDetected, RetryStormDetected, BudgetExceeded

config = SentinelConfig(loop_similarity_threshold=0.75, max_calls_per_session=20)
client = Sentinel(config=config)

session_id = "false-positive-test"

# These are all genuinely DIFFERENT questions - none should be blocked
questions = [
    "What is the capital of France?",
    "How do I bake a chocolate cake?",
    "What's the weather like on Mars?",
    "Explain how photosynthesis works.",
    "What year did World War 2 end?",
]

blocked_count = 0

for i, q in enumerate(questions, start=1):
    print(f"\n--- Message {i}: {q}")
    try:
        response = client.chat.completions.create(
            session_id=session_id,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": q}],
        )
        print("Response:", response.choices[0].message.content[:80])
    except LoopDetected as e:
        print("BLOCKED (WRONGLY!) - semantic loop:", e)
        blocked_count += 1
    except RetryStormDetected as e:
        print("BLOCKED - retry storm:", e)
    except BudgetExceeded as e:
        print("BLOCKED - budget exceeded:", e)

print(f"\n\nFalse positives: {blocked_count} out of {len(questions)} genuinely different questions were wrongly blocked.")
