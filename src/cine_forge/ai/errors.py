"""Shared AI transport errors."""


class LLMCallError(RuntimeError):
    """Terminal error for model invocation failures."""
