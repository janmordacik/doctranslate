"""Google Gemini API provider with API-key authentication."""

from __future__ import annotations

from .auth import ApiKeyAuth, OAuthTokenAuth
from .providers import HttpAiBackend


class GeminiBackend(HttpAiBackend):
    """Google Generative Language backend using the x-goog-api-key header."""

    provider_id = "gemini"
    name = "Gemini API"

    def __init__(self, model: str, *, base_url: str = "https://generativelanguage.googleapis.com/v1beta", **kwargs):
        super().__init__(model, base_url=base_url, **kwargs)

    def _auth_headers(self) -> dict[str, str]:
        if self.auth is None:
            raise RuntimeError("Gemini API requires credentials")
        token = self.auth.resolve(self.credential_store)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if isinstance(self.auth, OAuthTokenAuth):
            headers["Authorization"] = "Bearer " + token
        else:
            headers["x-goog-api-key"] = token
        return headers
    def _call_text(self, text: str, source_language: str, target_language: str) -> str:
        if self.auth is None:
            raise RuntimeError("Gemini API requires an API-key credential reference")
        value = self._post(
            "/models/" + self.model + ":generateContent",
            {"contents": [{"parts": [{"text": f"Translate from {source_language} to {target_language}. Return only translation.\n{text}"}]}]},
            headers=self._auth_headers(),
        )
        if not isinstance(value, dict):
            raise self._invalid()
        candidates = value.get("candidates")
        if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
            raise self._invalid()
        content = candidates[0].get("content")
        if not isinstance(content, dict) or not isinstance(content.get("parts"), list):
            raise self._invalid()
        parts = content["parts"]
        return self._string(parts[0].get("text") if parts and isinstance(parts[0], dict) else None, "candidates[0].content.parts[0].text")
    def list_models(self) -> tuple[str, ...]:
        if self.auth is None:
            raise RuntimeError("Gemini API requires an API-key credential reference")
        value = self._get(
            "/models",
            headers=self._auth_headers(),
        )
        data = value.get("models") if isinstance(value, dict) else None
        if not isinstance(data, list):
            raise self._invalid_models()
        return tuple(sorted(
            str(item["name"]).removeprefix("models/").strip()
            for item in data
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        )) if isinstance(data, list) else ()

    @staticmethod
    def _invalid():
        from .contracts import BackendError
        return BackendError("invalid_response", "Gemini response has no candidate text")
