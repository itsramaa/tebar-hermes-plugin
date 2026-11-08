"""Tool handlers for Tebar. Return structured tool_result/tool_error."""

from __future__ import annotations

import logging
from typing import Any

from tools.registry import tool_error, tool_result

from ..client import TebarClient
from ..client.exceptions import TebarAuthError, TebarError, TebarRateLimitError
from ..config import TebarConfig

__all__ = [
    "handle_tebar_accounts",
    "handle_tebar_create_post",
    "handle_tebar_list_posts",
    "handle_tebar_publish_post",
    "handle_tebar_insights",
]

logger = logging.getLogger(__name__)


def _client() -> TebarClient:
    return TebarClient(TebarConfig.from_env())


def _err(exc: TebarError, hint: str | None = None) -> str:
    details: dict[str, Any] = {}
    if exc.code:
        details["code"] = exc.code
    if exc.status:
        details["status"] = exc.status
    if isinstance(exc, TebarRateLimitError) and exc.retry_after is not None:
        details["retry_after_seconds"] = exc.retry_after
    if hint:
        details["hint"] = hint
    return tool_error(str(exc), **details)


def handle_tebar_accounts(args: dict, **kwargs: Any) -> str:
    del kwargs
    try:
        client = _client()
        payload: dict[str, Any] = {
            "accounts": client.list_accounts(
                limit=args.get("limit"), cursor=args.get("cursor")
            )
        }
        if args.get("include_me"):
            payload["me"] = client.get_me()
        return tool_result(payload)
    except TebarAuthError as exc:
        return _err(exc)
    except TebarError as exc:
        return _err(exc)


def handle_tebar_create_post(args: dict, **kwargs: Any) -> str:
    del kwargs
    content = args.get("content")
    account_ids = args.get("account_ids")
    if not isinstance(content, str) or not content.strip():
        return tool_error("content must be a non-empty string")
    if not isinstance(account_ids, list) or not account_ids:
        return tool_error("account_ids must be a non-empty list of account ID strings")

    scheduled_at = args.get("scheduled_at")
    if not scheduled_at and not args.get("confirmed"):
        return tool_error(
            "Publishing now is externally visible. Set confirmed=true only after "
            "the user explicitly confirms, or provide scheduled_at to schedule instead.",
            requires_confirmation=True,
            action="publish_now",
        )

    targets = [{"account_id": str(aid)} for aid in account_ids]
    try:
        result = _client().create_post(
            content=content,
            targets=targets,
            media_ids=args.get("media_ids"),
            media_urls=args.get("media_urls"),
            scheduled_at=scheduled_at,
        )
        return tool_result({"created": result, "scheduled": bool(scheduled_at)})
    except TebarAuthError as exc:
        return _err(exc)
    except TebarError as exc:
        return _err(exc)


def handle_tebar_list_posts(args: dict, **kwargs: Any) -> str:
    del kwargs
    try:
        return tool_result(
            _client().list_posts(
                limit=args.get("limit"),
                cursor=args.get("cursor"),
                account_id=args.get("account_id"),
                status=args.get("status"),
            )
        )
    except TebarAuthError as exc:
        return _err(exc)
    except TebarError as exc:
        return _err(exc)


def handle_tebar_publish_post(args: dict, **kwargs: Any) -> str:
    del kwargs
    post_id = args.get("post_id")
    if not isinstance(post_id, str) or not post_id.strip():
        return tool_error("post_id must be a non-empty string")
    if not args.get("confirmed"):
        return tool_error(
            "Publishing is externally visible and irreversible in effect. "
            "Set confirmed=true only after the user explicitly confirms.",
            requires_confirmation=True,
            action="publish_post",
            post_id=post_id,
        )
    try:
        return tool_result(
            {"published": _client().publish_post(post_id), "post_id": post_id}
        )
    except TebarAuthError as exc:
        return _err(exc)
    except TebarError as exc:
        return _err(exc)


def handle_tebar_insights(args: dict, **kwargs: Any) -> str:
    del kwargs
    account_id = args.get("account_id")
    if not isinstance(account_id, str) or not account_id.strip():
        return tool_error("account_id must be a non-empty string")
    try:
        return tool_result(
            _client().get_insights(
                account_id, since=args.get("since"), until=args.get("until")
            )
        )
    except TebarAuthError as exc:
        return _err(exc)
    except TebarError as exc:
        return _err(exc)
