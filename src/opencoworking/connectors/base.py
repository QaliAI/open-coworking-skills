"""Shared connector plumbing: transport protocol, retries, errors.

The Transport abstraction exists so every connector method is testable
against recorded fixtures without network access. HttpTransport is the
stdlib urllib implementation used in real runs.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol


class ConnectorError(Exception):
    """Structured connector failure. NEVER embeds credentials."""

    def __init__(self, kind: str, message: str, status: int | None = None):
        self.kind = kind          # auth | not_found | rate_limited | vendor | network
        self.status = status
        super().__init__(f"[{kind}] {message}" + (f" (HTTP {status})" if status else ""))


class Transport(Protocol):
    """Minimal HTTP transport. Returns (status, headers, body_bytes)."""

    def request(self, method: str, url: str, headers: dict[str, str],
                body: bytes | None = None,
                timeout: float = 30.0) -> tuple[int, dict[str, str], bytes]: ...


class HttpTransport:
    """stdlib urllib transport with a hard timeout."""

    def request(self, method: str, url: str, headers: dict[str, str],
                body: bytes | None = None,
                timeout: float = 30.0) -> tuple[int, dict[str, str], bytes]:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers or {}), e.read()
        except urllib.error.URLError as e:
            raise ConnectorError("network", f"request failed: {e.reason}") from None


def get_json(transport: Transport, url: str, headers: dict[str, str],
             max_retries: int = 3, timeout: float = 30.0) -> dict[str, Any]:
    """GET with retry/backoff on 429 and 5xx; auth/permission errors are
    raised immediately with credentials stripped from the message."""
    delay = 1.0
    for attempt in range(max_retries + 1):
        status, resp_headers, body = transport.request("GET", url, headers,
                                                       timeout=timeout)
        if status == 200:
            try:
                parsed = json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                raise ConnectorError("vendor", f"non-JSON response: {e}", status) from None
            if not isinstance(parsed, dict):
                return {"_list": parsed}
            return parsed
        if status in (401, 403):
            raise ConnectorError("auth",
                                 "authentication/permission failure - check the token "
                                 "and its scopes (token value not shown)", status)
        if status == 404:
            raise ConnectorError("not_found", f"resource not found: {url}", status)
        if status == 429 or 500 <= status < 600:
            if attempt == max_retries:
                kind = "rate_limited" if status == 429 else "vendor"
                raise ConnectorError(kind, f"gave up after {max_retries} retries", status)
            retry_after = resp_headers.get("Retry-After") or resp_headers.get("retry-after")
            try:
                wait = float(retry_after) if retry_after else delay
            except ValueError:
                wait = delay
            time.sleep(min(wait, 30.0))
            delay *= 2
            continue
        raise ConnectorError("vendor", f"unexpected response for {url}", status)
    raise ConnectorError("vendor", "unreachable")  # pragma: no cover


def encode_params(params: dict[str, str | int | None]) -> str:
    clean = {k: str(v) for k, v in params.items() if v is not None}
    return ("?" + urllib.parse.urlencode(clean)) if clean else ""
