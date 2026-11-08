"""Register Tebar slash commands with the Hermes plugin context."""

from __future__ import annotations

import logging
from typing import Any

from . import draft, status

__all__ = ["register_commands"]

logger = logging.getLogger(__name__)


def register_commands(ctx: Any) -> None:
    ctx.register_command(
        name="tebar-status",
        handler=status.make_handler(ctx),
        description="Check Tebar API key and summarize connected accounts.",
        args_hint="",
    )
    ctx.register_command(
        name="tebar-draft",
        handler=draft.make_handler(ctx),
        description="Generate a multi-platform social draft for a topic (never auto-publishes).",
        args_hint="<topic>",
    )
    logger.debug("tebar: registered /tebar-status and /tebar-draft")
