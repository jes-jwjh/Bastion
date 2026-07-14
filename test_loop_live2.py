from sentinel import Sentinel, SentinelConfig, LoopDetected, RetryStormDetected, BudgetExceeded

config = SentinelConfig(max_calls_per_session=10, loop_similarity_threshold=0.80)
client = Sentinel(config=config)

session_id = "live-loop-test-2"

questions = [
    "What is the capital of France?",
    "Can you tell me what France's capital city is?",
    "What's the capital of France, exactly?",
    "Tell me France's capital.",
]

for i, q in enumerate(questions, start=1):
    print(f"\n--- Message {i}: {q}")
    try:
        response = client.chat.completions.create(
            session_id=session_id,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": q}],
        )
        print("Response:", response.choices[0].message.content)
    except LoopDetected as e:
        print("BLOCKED - semantic loop:", e)
    except RetryStormDetected as e:
        print("BLOCKED - retry storm:", e)
    except BudgetExceeded as e:
        print("BLOCKED - budget exceeded:", e)
