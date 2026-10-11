"""Anthropic Claude Messages API provider."""

from __future__ import annotations

from .auth import ApiKeyAuth
from .providers import HttpAiBackend


class ClaudeBackend(HttpAiBackend):
    """Anthropic Messages API backend with provider-specific headers."""

    provider_id = "claude"
    name = "Claude API"

    def __init__(self, model: str, *, base_url: str = "https://api.anthropic.com", **kwargs):
        super().__init__(model, base_url=base_url, **kwargs)

    def _headers(self) -> dict[str, str]:
        if self.auth is None:
            raise RuntimeError("Claude API requires an API-key credential reference")
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.auth.resolve(self.credential_store),
            "anthropic-version": "2023-06-01",
        }

    def _call_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        *,
        target_variant: str = "auto",
    ) -> str:
        prompt = self._build_prompt(text, source_language, target_language, target_variant)
        return self._call_precomposed(prompt)

    def _call_precomposed(self, prompt):
        value = self._post("/v1/messages", {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": 0.2,
            "system": prompt.system,
            "messages": [{"role": "user", "content": prompt.user}],
        })
        if not isinstance(value, dict) or not isinstance(value.get("content"), list):
            raise self._invalid()
        content = value["content"]
        return self._string(content[0].get("text") if content and isinstance(content[0], dict) else None, "content[0].text")
    def list_models(self) -> tuple[str, ...]:
        value = self._get("/v1/models", headers=self._headers())
        data = value.get("data") if isinstance(value, dict) else None
        if not isinstance(data, list):
            raise self._invalid_models()
        return tuple(sorted(
            str(item["id"]).strip()
            for item in data
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        )) if isinstance(data, list) else ()

    @staticmethod
    def _invalid():
        from .contracts import BackendError
        return BackendError("invalid_response", "Claude response has no content[0].text")
