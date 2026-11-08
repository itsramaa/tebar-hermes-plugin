"""Tebar dashboard plugin — backend API routes.

Mounted at /api/plugins/tebar/ by the dashboard plugin system. Reuses the
existing tebar plugin package (config + client) so no HTTP logic is
duplicated. The api file is exec'd as a standalone module by the
dashboard server, so the plugin package is located dynamically below.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _load() -> Any:
    """Import the tebar plugin package in whichever context it exists."""
    try:
        return importlib.import_module("hermes_plugins.tebar")
    except Exception:
        pass
    plugins_dir = Path(__file__).resolve().parent.parent.parent
    if str(plugins_dir) not in sys.path:
        sys.path.insert(0, str(plugins_dir))
    return importlib.import_module("tebar")


_tebar = _load()
_pkg = _tebar.__name__
TebarConfig = importlib.import_module(f"{_pkg}.config").TebarConfig
TebarClient = importlib.import_module(f"{_pkg}.client").TebarClient
_exceptions = importlib.import_module(f"{_pkg}.client.exceptions")
TebarAuthError = _exceptions.TebarAuthError
TebarError = _exceptions.TebarError
TebarRateLimitError = _exceptions.TebarRateLimitError


def _config() -> TebarConfig:
    return TebarConfig.from_env()


def _client() -> TebarClient:
    return TebarClient(_config())


def _raise(exc: TebarError) -> None:
    if isinstance(exc, TebarAuthError):
        raise HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, TebarRateLimitError):
        raise HTTPException(status_code=429, detail=str(exc))
    raise HTTPException(status_code=502, detail=str(exc))


@router.get("/status")
async def status() -> Dict[str, Any]:
    config = _config()
    if not config.has_key:
        return {
            "configured": False,
            "profile_id": config.profile_id,
            "me": None,
            "error": "TEBAR_API_KEY belum diset - tambahkan di data/.env",
            "hint": "Set TEBAR_API_KEY=tb_live_... in data/.env, then restart the hermes container.",
        }
    try:
        me = _client().get_me()
    except TebarAuthError as exc:
        return {
            "configured": True,
            "profile_id": config.profile_id,
            "me": None,
            "error": str(exc),
        }
    except TebarError as exc:
        return {
            "configured": True,
            "profile_id": config.profile_id,
            "me": None,
            "error": str(exc),
        }
    return {
        "configured": True,
        "profile_id": config.profile_id,
        "me": me,
        "error": None,
    }


@router.get("/accounts")
async def accounts(
    limit: int = Query(default=50, le=100),
    cursor: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    config = _config()
    if not config.has_key:
        return {
            "configured": False,
            "data": [],
            "next_cursor": None,
            "error": "TEBAR_API_KEY belum diset - tambahkan di data/.env",
        }
    client = _client()
    try:
        result = client.list_accounts(limit=limit, cursor=cursor)
    except TebarAuthError as exc:
        return {"configured": True, "data": [], "next_cursor": None, "error": str(exc)}
    except TebarRateLimitError as exc:
        _raise(exc)
    except TebarError as exc:
        return {"configured": True, "data": [], "next_cursor": None, "error": str(exc)}

    accounts_list = result.get("data") if isinstance(result, dict) else result
    if not isinstance(accounts_list, list):
        accounts_list = []
    data = []
    for account in accounts_list:
        item: Dict[str, Any] = (
            dict(account) if isinstance(account, dict) else {"raw": account}
        )
        account_id = item.get("id")
        if account_id:
            try:
                item["publishing_limit"] = client.get_publishing_limit(str(account_id))
            except TebarError:
                item["publishing_limit"] = None
        data.append(item)
    next_cursor = result.get("next_cursor") if isinstance(result, dict) else None
    return {"configured": True, "data": data, "next_cursor": next_cursor, "error": None}


@router.get("/posts")
async def posts(
    limit: int = Query(default=20, le=100),
    cursor: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    config = _config()
    if not config.has_key:
        return {
            "configured": False,
            "data": [],
            "next_cursor": None,
            "error": "TEBAR_API_KEY belum diset - tambahkan di data/.env",
        }
    client = _client()
    try:
        result = client.list_posts(limit=limit, cursor=cursor, status=status)
    except TebarAuthError as exc:
        return {"configured": True, "data": [], "next_cursor": None, "error": str(exc)}
    except TebarRateLimitError as exc:
        _raise(exc)
    except TebarError as exc:
        return {"configured": True, "data": [], "next_cursor": None, "error": str(exc)}

    posts_list = result.get("data") if isinstance(result, dict) else result
    if not isinstance(posts_list, list):
        posts_list = []
    next_cursor = result.get("next_cursor") if isinstance(result, dict) else None
    return {
        "configured": True,
        "data": posts_list,
        "next_cursor": next_cursor,
        "error": None,
    }


class CreatePostBody(BaseModel):
    content: str
    account_ids: list
    scheduled_at: Optional[str] = None


@router.post("/posts")
async def create_post(body: CreatePostBody) -> Dict[str, Any]:
    content = (body.content or "").strip()
    account_ids = [str(a) for a in (body.account_ids or []) if str(a).strip()]
    if not content:
        raise HTTPException(status_code=400, detail="content must not be empty")
    if not account_ids:
        raise HTTPException(status_code=400, detail="account_ids must not be empty")
    targets = [{"account_id": a} for a in account_ids]
    client = _client()
    try:
        return client.create_post(
            content=content,
            targets=targets,
            scheduled_at=body.scheduled_at or None,
        )
    except TebarAuthError as exc:
        _raise(exc)
    except TebarRateLimitError as exc:
        _raise(exc)
    except TebarError as exc:
        _raise(exc)


@router.get("/insights/{account_id}")
async def insights(
    account_id: str,
    since: Optional[str] = Query(default=None),
    until: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    config = _config()
    if not config.has_key:
        return {
            "configured": False,
            "data": None,
            "error": "TEBAR_API_KEY belum diset - tambahkan di data/.env",
        }
    client = _client()
    try:
        data = client.get_insights(account_id, since=since, until=until)
    except TebarAuthError as exc:
        return {"configured": True, "data": None, "error": str(exc)}
    except TebarRateLimitError as exc:
        _raise(exc)
    except TebarError as exc:
        return {"configured": True, "data": None, "error": str(exc)}
    return {"configured": True, "data": data, "error": None}
