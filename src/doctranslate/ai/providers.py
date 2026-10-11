"""Common implementation for HTTP-based AI text providers."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Mapping, Sequence

from .auth import ApiKeyAuth, CredentialStore, MemoryCredentialStore
from .contracts import AiBackend, BackendError, ProbeResult, SegmentRequest, SegmentResult
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


    def list_models(self) -> tuple[str, ...]:
        """Return provider model IDs when the provider exposes discovery."""
        raise BackendError("model_discovery_unsupported", "Provider does not expose model discovery")

    def probe(self) -> ProbeResult:
        """Check endpoint, credentials and configured model without generation."""
        started = perf_counter()
        try:
            models = self.list_models()
            if models and self.model not in models:
                return ProbeResult(
                    self.provider_id, self.model, "model_not_found",
                    (perf_counter() - started) * 1000,
                    f"Configured model is not available: {self.model}",
                    "Choose a model returned by the provider or verify its model ID.",
                    models,
                )
            return ProbeResult(
                self.provider_id, self.model, "available",
                (perf_counter() - started) * 1000,
                "Provider endpoint, credentials and model are available.",
                models=models,
            )
        except BackendError as exc:
            return ProbeResult(
                self.provider_id, self.model, exc.code,
                (perf_counter() - started) * 1000,
                str(exc), exc.remedy,
            )
        except Exception:
            return ProbeResult(
                self.provider_id, self.model, "unavailable",
                (perf_counter() - started) * 1000,
                "Provider probe failed.",
                "Check endpoint, network access and provider configuration.",
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

    def _get(self, suffix: str, headers: Mapping[str, str] | None = None) -> object:
        response = self.transport.request(
            "GET",
            self.base_url + suffix,
            headers=headers or self._headers(),
            payload=None,
            timeout=self.timeout,
        )
        if not isinstance(response, HttpResponse):
            raise BackendError("invalid_transport", "Provider transport returned an invalid response")
        if response.status in (401, 403):
            raise BackendError("auth_required", "Provider authentication was rejected", remedy="configure credentials")
        if response.status == 404:
            raise BackendError("model_not_found", "Provider endpoint or model was not found", remedy="Check the endpoint and model ID.")
        if response.status == 429:
            raise BackendError("rate_limited", "Provider rate limit reached", retryable=True)
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
    def _invalid_models() -> BackendError:
        return BackendError("invalid_response", "Provider model list response is invalid")

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
