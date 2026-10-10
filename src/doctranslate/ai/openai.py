"""OpenAI official API provider (API key authentication only in this phase)."""

from __future__ import annotations

from .auth import ApiKeyAuth
from .providers import HttpAiBackend


class OpenAIBackend(HttpAiBackend):
    """OpenAI-compatible chat-completions backend using API-key auth."""

    provider_id = "openai"
    name = "OpenAI API"

    def __init__(self, model: str, *, base_url: str = "https://api.openai.com/v1", **kwargs):
        super().__init__(model, base_url=base_url, **kwargs)

    def _call_text(self, text: str, source_language: str, target_language: str) -> str:
        value = self._post("/chat/completions", {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": f"Translate from {source_language} to {target_language}. Return only translation."},
                {"role": "user", "content": text},
            ],
        })
        if not isinstance(value, dict):
            raise self._invalid()
        choices = value.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise self._invalid()
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise self._invalid()
        return self._string(message.get("content"), "choices[0].message.content")

    @staticmethod
    def _invalid():
        from .contracts import BackendError
        return BackendError("invalid_response", "OpenAI response has no choices[0].message.content")
