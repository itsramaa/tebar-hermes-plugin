"""Register Tebar tools with the Hermes plugin context."""

from __future__ import annotations

import logging
from typing import Any

from .handlers import (
    handle_tebar_accounts,
    handle_tebar_create_post,
    handle_tebar_insights,
    handle_tebar_list_posts,
    handle_tebar_publish_post,
)
from .schemas import (
    TEBAR_ACCOUNTS_SCHEMA,
    TEBAR_CREATE_POST_SCHEMA,
    TEBAR_INSIGHTS_SCHEMA,
    TEBAR_LIST_POSTS_SCHEMA,
    TEBAR_PUBLISH_POST_SCHEMA,
)

__all__ = ["register_tools"]

logger = logging.getLogger(__name__)

_TOOLS = [
    (
        "tebar_accounts",
        TEBAR_ACCOUNTS_SCHEMA,
        handle_tebar_accounts,
        "List connected Tebar accounts and optional authenticated user.",
    ),
    (
        "tebar_create_post",
        TEBAR_CREATE_POST_SCHEMA,
        handle_tebar_create_post,
        "Create a Tebar post (schedule via scheduled_at or publish now with explicit confirmation).",
    ),
    (
        "tebar_list_posts",
        TEBAR_LIST_POSTS_SCHEMA,
        handle_tebar_list_posts,
        "List Tebar posts with optional filters and pagination.",
    ),
    (
        "tebar_publish_post",
        TEBAR_PUBLISH_POST_SCHEMA,
        handle_tebar_publish_post,
        "Publish an existing Tebar post now (irreversible externally; user confirmation required).",
    ),
    (
        "tebar_insights",
        TEBAR_INSIGHTS_SCHEMA,
        handle_tebar_insights,
        "Fetch performance insights for a Tebar account.",
    ),
]


def register_tools(ctx: Any) -> None:
    for name, schema, handler, description in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="tebar",
            schema=schema,
            handler=handler,
            description=description,
            requires_env=["TEBAR_API_KEY"],
        )
    logger.debug("tebar: registered %d tools", len(_TOOLS))
