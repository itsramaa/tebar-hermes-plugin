"""Insights-related Tebar endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

__all__ = ["InsightsMixin"]


class InsightsMixin:
    """GET /accounts/{id}/insights and /accounts/{id}/posts."""

    def get_insights(
        self,
        account_id: str,
        *,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {"since": since, "until": until}
        return self.get(f"/accounts/{account_id}/insights", params)  # type: ignore[attr-defined]

    def get_account_posts(
        self,
        account_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {"limit": limit, "cursor": cursor}
        return self.get(f"/accounts/{account_id}/posts", params)  # type: ignore[attr-defined]
