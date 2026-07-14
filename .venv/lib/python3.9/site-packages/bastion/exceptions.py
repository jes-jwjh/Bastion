class BastionBlocked(Exception):
    """Base class for anything Bastion blocks before it reaches the model provider."""


class LoopDetected(BastionBlocked):
    """Raised when the semantic loop detector catches a paraphrased repeat loop."""


class RetryStormDetected(BastionBlocked):
    """Raised when too many calls happen in too short a window (cooldown enforced)."""


class BudgetExceeded(BastionBlocked):
    """Raised when a session's cost or call-count cap is hit."""
