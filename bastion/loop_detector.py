"""
Semantic Loop Detector (V2 core feature).
"""

from collections import deque, defaultdict
from math import sqrt

from .config import BastionConfig
from .exceptions import LoopDetected


def _cosine_similarity(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class LoopDetector:
    def __init__(self, config: BastionConfig, embed_fn):
        self.config = config
        self.embed_fn = embed_fn
        self._history = defaultdict(lambda: deque(maxlen=config.loop_window_size))
        self._repeat_counts = defaultdict(int)

    def check(self, session_id: str, prompt_text: str) -> None:
        embedding = self.embed_fn(prompt_text)
        history = self._history[session_id]

        is_duplicate_of_recent = False
        for _, past_embedding in history:
            similarity = _cosine_similarity(embedding, past_embedding)
            if similarity >= self.config.loop_similarity_threshold:
                is_duplicate_of_recent = True
                break

        if is_duplicate_of_recent:
            self._repeat_counts[session_id] += 1
        else:
            self._repeat_counts[session_id] = 0

        history.append((prompt_text, embedding))

        if self._repeat_counts[session_id] >= self.config.loop_repeat_trigger:
            raise LoopDetected(
                f"Session '{session_id}' repeated a semantically similar "
                f"request {self._repeat_counts[session_id]} times in a row. "
                f"Session killed to prevent a reasoning loop."
            )

    def reset(self, session_id: str) -> None:
        self._history.pop(session_id, None)
        self._repeat_counts.pop(session_id, None)
