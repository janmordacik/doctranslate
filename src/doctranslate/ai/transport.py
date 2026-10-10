"""Minimal standard-library HTTP transport shared by provider plugins."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping
from urllib import error, request

from .contracts import BackendError


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: object


class UrllibTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] = (),
        payload: object | None = None,
        timeout: float = 120,
    ) -> HttpResponse:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, method=method, headers=dict(headers))
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return HttpResponse(response.status, dict(response.headers), body)
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"error": raw}
            return HttpResponse(exc.code, dict(exc.headers or {}), body)
        except (OSError, TimeoutError) as exc:
            raise BackendError("network_error", str(exc), retryable=True) from exc
