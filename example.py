from bastion import Bastion, LoopDetected, RetryStormDetected, BudgetExceeded

client = Bastion()

session_id = "demo-session-1"

try:
    response = client.chat.completions.create(
        session_id=session_id,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Summarize the plot of Hamlet in two sentences."}],
    )
    print(response.choices[0].message.content)
    print("Session stats:", client.get_session_stats(session_id))

except LoopDetected as e:
    print("Blocked - semantic loop:", e)
except RetryStormDetected as e:
    print("Blocked - retry storm:", e)
except BudgetExceeded as e:
    print("Blocked - budget exceeded:", e)
