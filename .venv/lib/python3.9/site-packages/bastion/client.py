"""
Bastion — a lightweight runtime protection layer for AI agents.
"""

from openai import OpenAI

from .config import BastionConfig
from .loop_detector import LoopDetector
from .retry_storm import RetryStormDetector
from .budget import BudgetCircuitBreaker


class _ChatCompletions:
    def __init__(self, sentinel: "Bastion"):
        self._sentinel = sentinel

    def create(self, *, session_id: str, messages, model="gpt-4o-mini", **kwargs):
        s = self._sentinel

        s.retry_storm.check(session_id)
        s.budget.check_before_call(session_id)

        latest_user_text = _extract_latest_user_text(messages)
        if latest_user_text:
            s.loop_detector.check(session_id, latest_user_text)

        response = s._openai.chat.completions.create(model=model, messages=messages, **kwargs)

        usage = response.usage
        cost = s.budget.record_after_call(
            session_id,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
        s._last_cost_by_session[session_id] = cost
        return response


class _Chat:
    def __init__(self, sentinel: "Bastion"):
        self.completions = _ChatCompletions(sentinel)


class Bastion:
    def __init__(self, openai_api_key: str = None, config: BastionConfig = None):
        self._openai = OpenAI(api_key=openai_api_key) if openai_api_key else OpenAI()
        self.config = config or BastionConfig()

        self.loop_detector = LoopDetector(self.config, embed_fn=self._embed)
        self.retry_storm = RetryStormDetector(self.config)
        self.budget = BudgetCircuitBreaker(self.config)

        self._last_cost_by_session = {}
        self.chat = _Chat(self)

    def _embed(self, text: str):
        result = self._openai.embeddings.create(
            model=self.config.embedding_model,
            input=text,
        )
        return result.data[0].embedding

    def get_session_stats(self, session_id: str) -> dict:
        return self.budget.get_session_stats(session_id)

    def reset_session(self, session_id: str) -> None:
        self.loop_detector.reset(session_id)
        self.retry_storm.reset(session_id)
        self.budget.reset(session_id)
        self._last_cost_by_session.pop(session_id, None)


def _extract_latest_user_text(messages) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""
