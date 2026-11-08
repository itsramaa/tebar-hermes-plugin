"""Post-related Tebar endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["PostsMixin"]


class PostsMixin:
    """POST/GET/PATCH/DELETE on /posts plus /posts/{id}/publish."""

    def create_post(
        self,
        *,
        content: str,
        targets: List[Dict[str, Any]],
        media_ids: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> Any:
        body: Dict[str, Any] = {"content": content, "targets": targets}
        if media_ids:
            body["media_ids"] = media_ids
        if media_urls:
            body["media_urls"] = media_urls
        if scheduled_at:
            body["scheduled_at"] = scheduled_at
        return self.post("/posts", body)  # type: ignore[attr-defined]

    def list_posts(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "account_id": account_id,
            "status": status,
        }
        return self.get("/posts", params)  # type: ignore[attr-defined]

    def get_post(self, post_id: str) -> Any:
        return self.get(f"/posts/{post_id}")  # type: ignore[attr-defined]

    def update_post(
        self,
        post_id: str,
        *,
        content: Optional[str] = None,
        scheduled_at: Optional[str] = None,
    ) -> Any:
        body: Dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if scheduled_at is not None:
            body["scheduled_at"] = scheduled_at
        return self.patch(f"/posts/{post_id}", body)  # type: ignore[attr-defined]

    def publish_post(self, post_id: str) -> Any:
        return self.post(f"/posts/{post_id}/publish")  # type: ignore[attr-defined]

    def delete_post(self, post_id: str) -> Any:
        return self.delete(f"/posts/{post_id}")  # type: ignore[attr-defined]
