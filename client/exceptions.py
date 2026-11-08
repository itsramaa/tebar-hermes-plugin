"""Typed exceptions for the Tebar client."""

from __future__ import annotations

from typing import Optional

__all__ = ["TebarError", "TebarAuthError", "TebarRateLimitError"]


class TebarError(Exception):
    """Base error for any Tebar API or transport failure."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class TebarAuthError(TebarError):
    """Authentication/authorization failure (HTTP 401/403) or missing key."""


class TebarRateLimitError(TebarError):
    """HTTP 429 — carries the server's rate-limit reset hint when present."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status: Optional[int] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, code=code, status=status)
        self.retry_after = retry_after
