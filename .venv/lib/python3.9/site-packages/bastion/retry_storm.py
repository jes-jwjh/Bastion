"""
API Retry Storm Detector.
"""

import time
from collections import defaultdict, deque

from .config import BastionConfig
from .exceptions import RetryStormDetected


class RetryStormDetector:
    def __init__(self, config: BastionConfig):
        self.config = config
        self._call_times = defaultdict(deque)
        self._cooldown_until = defaultdict(float)

    def check(self, session_id: str) -> None:
        now = time.monotonic()

        if now < self._cooldown_until[session_id]:
            remaining = round(self._cooldown_until[session_id] - now, 2)
            raise RetryStormDetected(
                f"Session '{session_id}' is in cooldown for another "
                f"{remaining}s after a retry storm was detected."
            )

        times = self._call_times[session_id]
        times.append(now)

        window_start = now - self.config.retry_window_seconds
        while times and times[0] < window_start:
            times.popleft()

        if len(times) > self.config.retry_max_calls:
            self._cooldown_until[session_id] = now + self.config.retry_cooldown_seconds
            times.clear()
            raise RetryStormDetected(
                f"Session '{session_id}' made more than "
                f"{self.config.retry_max_calls} calls within "
                f"{self.config.retry_window_seconds}s. Cooldown of "
                f"{self.config.retry_cooldown_seconds}s enforced."
            )

    def reset(self, session_id: str) -> None:
        self._call_times.pop(session_id, None)
        self._cooldown_until.pop(session_id, None)
