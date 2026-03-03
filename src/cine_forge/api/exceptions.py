"""Shared exceptions for the CineForge API layer."""

from __future__ import annotations


class ServiceError(Exception):
    """Service-level error with API-ready details."""

    def __init__(self, code: str, message: str, hint: str | None = None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status_code = status_code
