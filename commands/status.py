"""`/tebar-status` — check API key + account summary."""

from __future__ import annotations

import logging
from typing import Any

from ..client import TebarClient
from ..client.exceptions import TebarAuthError, TebarError
from ..config import TebarConfig

__all__ = ["make_handler"]

logger = logging.getLogger(__name__)


def make_handler(ctx: Any):
    del ctx  # reserved for future LLM usage / context

    def handler(raw_args: str) -> str:
        del raw_args
        config = TebarConfig.from_env()
        if not config.has_key:
            return f"{config.missing_key_message()}"

        client = TebarClient(config)
        try:
            accounts = client.list_accounts()
            me = client.get_me()
        except TebarAuthError as exc:
            return f"Tebar auth error: {exc}"
        except TebarError as exc:
            return f"Tebar error: {exc}"

        account_list = _as_list(accounts)
        profile = _profile_line(config.profile_id, me)
        return (
            "Tebar API key is set. "
            f"Connected accounts: {len(account_list)}.\n"
            f"Profile: {profile}\n"
            f"Accounts: {_format_accounts(account_list)}"
        )

    return handler


def _as_list(payload: Any) -> list:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload, list):
        return payload
    return []


def _profile_line(profile_id: str | None, me: Any) -> str:
    if profile_id:
        return profile_id
    if isinstance(me, dict):
        handle = me.get("handle") or me.get("id") or me.get("name")
        return str(handle) if handle else "(no id)"
    return "(unknown)"


def _format_accounts(accounts: list) -> str:
    if not accounts:
        return "(none)"
    lines = []
    for a in accounts[:10]:
        if not isinstance(a, dict):
            continue
        account_id = a.get("id") or "?"
        platform = a.get("platform") or "?"
        name = a.get("handle") or a.get("name") or "?"
        lines.append(f"  - {account_id} ({platform}) {name}")
    extra = f"\n  ... and {len(accounts) - 10} more" if len(accounts) > 10 else ""
    return "\n".join(lines) + extra if lines else "(none)"
