"""JSON Schemas for Tebar tools."""

from __future__ import annotations

__all__ = [
    "TEBAR_ACCOUNTS_SCHEMA",
    "TEBAR_CREATE_POST_SCHEMA",
    "TEBAR_LIST_POSTS_SCHEMA",
    "TEBAR_PUBLISH_POST_SCHEMA",
    "TEBAR_INSIGHTS_SCHEMA",
]

TEBAR_ACCOUNTS_SCHEMA = {
    "description": (
        "List connected Tebar social accounts (ids, platforms, names) and "
        "optionally include the authenticated user. Use to discover account_id "
        "values before creating posts or fetching insights."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "include_me": {
                "type": "boolean",
                "description": "Also fetch /me (the authenticated Tebar user). Default false.",
            },
            "limit": {
                "type": "integer",
                "description": "Page size (max 100).",
                "minimum": 1,
                "maximum": 100,
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor from a previous response.",
            },
        },
        "additionalProperties": False,
    },
}

TEBAR_CREATE_POST_SCHEMA = {
    "description": (
        "Create a Tebar post. With scheduled_at (ISO 8601, timezone required) "
        "it schedules the post; without scheduled_at it publishes NOW "
        "(externally visible). Confirm with the user before publishing now or "
        "when targets/content are ambiguous. Returns post id and status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Post body text.",
            },
            "account_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Target Tebar account IDs to publish to.",
                "minItems": 1,
            },
            "media_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional uploaded media IDs.",
            },
            "media_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional media URLs.",
            },
            "scheduled_at": {
                "type": "string",
                "description": "ISO 8601 datetime with timezone to schedule (omit to publish now).",
            },
            "confirmed": {
                "type": "boolean",
                "description": (
                    "Set true only after the user explicitly confirms an immediate "
                    "publish (required when scheduled_at is omitted)."
                ),
            },
        },
        "required": ["content", "account_ids"],
        "additionalProperties": False,
    },
}

TEBAR_LIST_POSTS_SCHEMA = {
    "description": "List Tebar posts with optional filters and pagination.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Page size (max 100).",
                "minimum": 1,
                "maximum": 100,
            },
            "cursor": {"type": "string", "description": "Pagination cursor."},
            "account_id": {"type": "string", "description": "Filter by account ID."},
            "status": {"type": "string", "description": "Filter by post status."},
        },
        "additionalProperties": False,
    },
}

TEBAR_PUBLISH_POST_SCHEMA = {
    "description": (
        "Publish an existing Tebar post NOW (externally visible/irreversible "
        "distribution). Requires explicit user confirmation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "The Tebar post ID to publish.",
            },
            "confirmed": {
                "type": "boolean",
                "description": "Must be true after explicit user confirmation.",
            },
        },
        "required": ["post_id", "confirmed"],
        "additionalProperties": False,
    },
}

TEBAR_INSIGHTS_SCHEMA = {
    "description": "Fetch performance insights for a Tebar account.",
    "parameters": {
        "type": "object",
        "properties": {
            "account_id": {"type": "string", "description": "Tebar account ID."},
            "since": {"type": "string", "description": "ISO 8601 start (optional)."},
            "until": {"type": "string", "description": "ISO 8601 end (optional)."},
        },
        "required": ["account_id"],
        "additionalProperties": False,
    },
}
