"""Tebar configuration.

Reads credentials and tuning knobs from the environment. No secrets are
ever emitted to logs, error text, or tool responses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

__all__ = ["TebarConfig", "DEFAULT_BASE_URL", "DEFAULT_TIMEOUT"]

DEFAULT_BASE_URL = "https://api.tebar.app/v1"
DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class TebarConfig:
    api_key: str
    profile_id: Optional[str]
    timeout: int
    base_url: str

    @classmethod
    def from_env(cls) -> "TebarConfig":
        try:
            timeout = int(os.environ.get("TEBAR_TIMEOUT", DEFAULT_TIMEOUT))
        except (TypeError, ValueError):
            timeout = DEFAULT_TIMEOUT
        return cls(
            api_key=os.environ.get("TEBAR_API_KEY", ""),
            profile_id=os.environ.get("TEBAR_PROFILE_ID") or None,
            timeout=max(1, timeout),
            base_url=DEFAULT_BASE_URL,
        )

    @property
    def has_key(self) -> bool:
        return bool(self.api_key.strip())

    def missing_key_message(self) -> str:
        return (
            "TEBAR_API_KEY is not set. Add it to your environment "
            "(e.g. data/.env) as TEBAR_API_KEY=tb_live_..."
        )

    def auth_headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if self.profile_id:
            headers["Tebar-Profile"] = self.profile_id
        return headers
