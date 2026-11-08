"""Tebar plugin entry point."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Register Tebar tools and slash commands."""
    from .tools import register_tools
    from .commands import register_commands

    register_tools(ctx)
    register_commands(ctx)
    logger.debug("tebar: registered tools and commands")
