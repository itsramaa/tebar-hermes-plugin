"""Base HTTP client for the Tebar API (stdlib urllib only)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional

from ..config import TebarConfig
from .exceptions import TebarAuthError, TebarError, TebarRateLimitError

__all__ = ["TebarBaseClient"]

logger = logging.getLogger(__name__)

_WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
_MAX_ATTEMPTS = 3
_MAX_BACKOFF_SECONDS = 30.0


class TebarBaseClient:
    """Low-level Tebar transport: auth, idempotency, retry, JSON, typed errors.

    One-way dependency: this module imports only config + exceptions.
    """

    def __init__(self, config: TebarConfig) -> None:
        self._config = config
        self._timeout = config.timeout

    @property
    def config(self) -> TebarConfig:
        return self._config

    # -- public verb helpers -------------------------------------------------

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", path, body=body)

    def patch(self, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PATCH", path, body=body)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("DELETE", path, params=params)

    # -- transport -----------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        attempts: int = _MAX_ATTEMPTS,
    ) -> Any:
        if not self._config.has_key:
            raise TebarAuthError(self._config.missing_key_message(), code="missing_key")

        url = self._build_url(path, params)
        headers = self._build_headers(method)
        payload: Optional[bytes] = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        last_exc: Optional[TebarError] = None
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(
                url, data=payload, headers=headers, method=method
            )
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as resp:
                    return self._decode(resp.read())
            except urllib.error.HTTPError as exc:
                error = self._http_error(exc)
                if isinstance(error, TebarRateLimitError) and attempt < attempts:
                    delay = error.retry_after or min(2.0**attempt, _MAX_BACKOFF_SECONDS)
                    logger.warning(
                        "tebar: rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt,
                        attempts,
                        delay,
                    )
                    time.sleep(min(delay, _MAX_BACKOFF_SECONDS))
                    last_exc = error
                    continue
                raise error
            except urllib.error.URLError as exc:
                raise TebarError(f"Tebar request failed: {exc.reason}") from exc
            except TimeoutError as exc:
                raise TebarError("Tebar request timed out") from exc

        raise last_exc or TebarError("Tebar request failed")

    def _build_url(self, path: str, params: Optional[Dict[str, Any]]) -> str:
        url = f"{self._config.base_url}{path}"
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        if clean:
            url = f"{url}?{urllib.parse.urlencode(clean)}"
        return url

    def _build_headers(self, method: str) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        headers.update(self._config.auth_headers())
        if method.upper() in _WRITE_METHODS:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        return headers

    def _decode(self, raw: bytes) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise TebarError("Tebar returned a non-JSON response") from exc

    def _http_error(self, exc: urllib.error.HTTPError) -> TebarError:
        status = exc.code
        code: Optional[str] = None
        message = f"Tebar API error (HTTP {status})"
        retry_after: Optional[float] = None
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            error = payload.get("error") if isinstance(payload, dict) else None
            if isinstance(error, dict):
                code = error.get("code")
                message = error.get("message") or message
            elif isinstance(payload, dict) and payload.get("message"):
                message = payload["message"]
        except Exception:  # noqa: BLE001 — best-effort body parse
            pass

        if status == 429:
            retry_after = self._retry_after(exc)
            return TebarRateLimitError(
                message,
                code=code or "rate_limited",
                status=status,
                retry_after=retry_after,
            )
        if status in (401, 403):
            return TebarAuthError(message, code=code, status=status)
        return TebarError(message, code=code, status=status)

    @staticmethod
    def _retry_after(exc: urllib.error.HTTPError) -> Optional[float]:
        reset = exc.headers.get("RateLimit-Reset") or exc.headers.get("Retry-After")
        if not reset:
            return None
        try:
            return float(reset)
        except (TypeError, ValueError):
            return None
