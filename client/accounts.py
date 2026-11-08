"""Account-related Tebar endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

__all__ = ["AccountsMixin"]


class AccountsMixin:
    """GET /me, /accounts, /accounts/{id}/publishing-limit."""

    def get_me(self) -> Any:
        return self.get("/me")  # type: ignore[attr-defined]

    def list_accounts(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        params: Dict[str, Any] = {"limit": limit, "cursor": cursor}
        return self.get("/accounts", params)  # type: ignore[attr-defined]

    def get_publishing_limit(self, account_id: str) -> Any:
        return self.get(f"/accounts/{account_id}/publishing-limit")  # type: ignore[attr-defined]
