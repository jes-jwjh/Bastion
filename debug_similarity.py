from sentinel import Sentinel
from math import sqrt

client = Sentinel()

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)

questions = [
    "What is the capital of France?",
    "Can you tell me what France's capital city is?",
    "What's the capital of France, exactly?",
    "Tell me France's capital.",
]

embeddings = [client._embed(q) for q in questions]

print("Similarity scores vs Message 1:")
for i in range(1, len(questions)):
    sim = cosine_similarity(embeddings[0], embeddings[i])
    print(f"  Message 1 vs Message {i+1}: {sim:.4f}")
