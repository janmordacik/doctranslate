"""Common implementation for HTTP-based AI text providers."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .auth import ApiKeyAuth, CredentialStore, MemoryCredentialStore
from .contracts import AiBackend, BackendError, SegmentRequest, SegmentResult
from .transport import HttpResponse, UrllibTransport


class HttpAiBackend(AiBackend):
    """Provider base with safe response validation and a mockable transport."""

    provider_id = "http"
    name = "HTTP AI"

    def __init__(
        self,
        model: str,
        *,
        base_url: str,
        transport: object | None = None,
        credential_store: CredentialStore | None = None,
        auth: ApiKeyAuth | None = None,
        timeout: float = 120,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrllibTransport()
        self.credential_store = credential_store or MemoryCredentialStore()
        self.auth = auth
        self.timeout = timeout

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        """Translate one text value and reject an empty provider response."""
        result = self._call_text(text, source_language, target_language)
        if not isinstance(result, str) or not result.strip():
            raise BackendError("empty_output", "Provider returned no translated text")
        return result

    def translate_segments(self, requests: Sequence[SegmentRequest]) -> Sequence[SegmentResult]:
        """Translate ordered segments without changing their identifiers."""
        return tuple(
            SegmentResult(
                request.segment_id,
                self.translate(request.text, request.source_language, request.target_language),
            )
            for request in requests
        )

    def _call_text(self, text: str, source_language: str, target_language: str) -> str:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.auth is not None:
            headers["Authorization"] = "Bearer " + self.auth.resolve(self.credential_store)
        return headers

    def _post(self, suffix: str, payload: Mapping[str, Any], headers: Mapping[str, str] | None = None) -> object:
        response = self.transport.request(
            "POST",
            self.base_url + suffix,
            headers=headers or self._headers(),
            payload=payload,
            timeout=self.timeout,
        )
        if not isinstance(response, HttpResponse):
            raise BackendError("invalid_transport", "Provider transport returned an invalid response")
        if response.status in (401, 403):
            raise BackendError("auth_required", "Provider authentication was rejected", remedy="configure credentials")
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            raise BackendError(
                "rate_limited",
                "Provider rate limit reached",
                retryable=True,
                retry_after=float(retry_after) if retry_after and retry_after.isdigit() else None,
            )
        if response.status >= 500:
            raise BackendError("service_unavailable", "Provider service is unavailable", retryable=True)
        if response.status >= 400:
            raise BackendError("provider_error", f"Provider request failed with HTTP {response.status}")
        return response.body

    @staticmethod
    def _string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise BackendError("invalid_response", f"Provider response has no {label}")
        return value

    @staticmethod
    def _json_segments(value: str, requests: Sequence[SegmentRequest]) -> tuple[SegmentResult, ...]:
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise BackendError("invalid_response", "Provider did not return JSON segments") from exc
        if not isinstance(decoded, list):
            raise BackendError("invalid_response", "Provider segment response must be a list")
        results = []
        for item in decoded:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("text"), str):
                raise BackendError("invalid_response", "Provider returned an invalid segment")
            results.append(SegmentResult(item["id"], item["text"]))
        return tuple(results)
