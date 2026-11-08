"""`/tebar-draft <topic>` — LLM-generated multi-platform draft. Never auto-publishes."""

from __future__ import annotations

import logging
from typing import Any

from ..client import TebarClient
from ..client.exceptions import TebarAuthError, TebarError
from ..config import TebarConfig

__all__ = ["make_handler", "DRAFT_SCHEMA"]

logger = logging.getLogger(__name__)

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "x_short": {
            "type": "string",
            "description": "X / Twitter post (<= 280 chars).",
        },
        "threads": {
            "type": "string",
            "description": "Threads / Facebook post (multi-paragraph ok).",
        },
        "ig_caption": {
            "type": "string",
            "description": "Instagram caption with 1-3 hashtags.",
        },
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of hashtags.",
        },
        "notes": {
            "type": "string",
            "description": "Optional caveat or follow-up suggestion.",
        },
    },
    "required": ["x_short", "threads", "ig_caption"],
    "additionalProperties": False,
}

_DRAFT_INSTRUCTIONS = (
    "Produce a multi-platform social media draft for the given topic. "
    "Keep `x_short` under 280 characters. `threads` may be 1-3 short paragraphs "
    "with a call-to-action. `ig_caption` should be friendly and end with 1-3 "
    "hashtags. Return only the structured record."
)


def make_handler(ctx: Any):
    def handler(raw_args: str) -> str:
        topic = (raw_args or "").strip()
        if not topic:
            return "Usage: /tebar-draft <topic>"

        config = TebarConfig.from_env()
        if not config.has_key:
            return config.missing_key_message()

        # Fetch accounts first so the draft can be tailored to platforms present.
        try:
            payload = TebarClient(config).list_accounts(limit=50)
            accounts = _as_list(payload)
        except TebarAuthError as exc:
            return f"Tebar auth error while listing accounts: {exc}"
        except TebarError as exc:
            return f"Tebar error while listing accounts: {exc}"

        platforms = sorted(
            {a.get("platform", "?") for a in accounts if isinstance(a, dict)}
        )
        accounts_context = ", ".join(platforms) if platforms else "(no accounts yet)"

        try:
            result = ctx.llm.complete_structured(
                instructions=_DRAFT_INSTRUCTIONS,
                input=[
                    {
                        "type": "text",
                        "text": (
                            f"Topic: {topic}\n"
                            f"Available connected platforms: {accounts_context}\n"
                            "Generate the draft record. Do NOT publish anything."
                        ),
                    }
                ],
                json_schema=DRAFT_SCHEMA,
                schema_name="tebar.draft",
                purpose="tebar-plugin.draft",
                temperature=0.4,
                max_tokens=600,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("tebar-draft LLM call failed: %s", exc)
            return f"Draft generation failed: {exc}"

        if result.parsed is not None:
            return _format_draft(
                result.parsed, platforms, result.provider, result.model
            )

        return (
            f"Model did not return parseable JSON.\n"
            f"Raw response from {result.provider}/{result.model}:\n"
            f"---\n{result.text}\n---"
        )

    return handler


def _as_list(payload: Any) -> list:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload, list):
        return payload
    return []


def _format_draft(parsed: dict, platforms: list, provider: str, model: str) -> str:
    x_short = parsed.get("x_short", "").strip()
    threads = parsed.get("threads", "").strip()
    ig_caption = parsed.get("ig_caption", "").strip()
    hashtags = parsed.get("hashtags") or []
    notes = parsed.get("notes", "").strip()

    sections = [
        f"# Tebar draft (via {provider}/{model}, platforms: {', '.join(platforms) or 'n/a'})",
        f"## X (<=280 chars, {len(x_short)}/{280})",
        x_short,
        "## Threads / Facebook",
        threads,
        "## Instagram caption",
        ig_caption,
    ]
    if hashtags:
        sections.append("## Hashtags")
        sections.append(
            "  "
            + " ".join(
                f"#{h.strip() if not h.startswith('#') else h}" for h in hashtags
            )
        )
    if notes:
        sections.append(f"## Notes\n{notes}")

    sections.append("")
    sections.append(
        "Draft only — NOT published. To schedule or publish, use the "
        "`tebar_create_post` tool with `confirmed=true` ONLY after you "
        "explicitly confirm."
    )
    return "\n\n".join(sections)
