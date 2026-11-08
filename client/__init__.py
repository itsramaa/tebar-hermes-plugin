"""Composed Tebar API client."""

from __future__ import annotations

from .accounts import AccountsMixin
from .base import TebarBaseClient
from .insights import InsightsMixin
from .posts import PostsMixin

__all__ = ["TebarClient"]


class TebarClient(AccountsMixin, PostsMixin, InsightsMixin, TebarBaseClient):
    """Full Tebar client. `Accounts/Posts/InsightsMixin + TebarBaseClient`."""

    pass
