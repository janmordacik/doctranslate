"""Explicit provider registry and lazy discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .auth import CredentialStore
from .profiles import AiProfile


@dataclass(frozen=True)
class ProviderDescriptor:
    """Factory and capabilities exposed by one selectable AI provider."""

    provider_id: str
    label: str
    factory: Callable[[AiProfile, CredentialStore], object]
    capabilities: tuple[str, ...] = ("text", "segments")
    auth_methods: tuple[str, ...] = ("none",)
    configuration_supported: bool = False
    login_supported: bool = False
    model_discovery_supported: bool = False


class ProviderRegistry:
    """Explicit registry preventing provider discovery from changing at runtime."""

    def __init__(self) -> None:
        self._items: dict[str, ProviderDescriptor] = {}

    def register(self, descriptor: ProviderDescriptor) -> None:
        """Register one provider and reject accidental duplicate identifiers."""
        if descriptor.provider_id in self._items:
            raise ValueError(f"Duplicate provider: {descriptor.provider_id}")
        self._items[descriptor.provider_id] = descriptor

    def list(self) -> tuple[ProviderDescriptor, ...]:
        """Return descriptors in stable identifier order for CLI and GUI."""
        return tuple(sorted(self._items.values(), key=lambda item: item.provider_id))

    def get(self, provider_id: str) -> ProviderDescriptor:
        """Resolve a provider or raise a clear error before a job starts."""
        try:
            return self._items[provider_id]
        except KeyError as exc:
            raise LookupError(f"Unknown provider: {provider_id}") from exc

    def create(self, profile: AiProfile, credentials: CredentialStore):
        """Construct a backend from a non-secret profile and credential store."""
        return self.get(profile.provider_id).factory(profile, credentials)


def build_default_provider_registry() -> ProviderRegistry:
    """Build the built-in registry; imports stay lazy until a provider is used."""
    registry = ProviderRegistry()

    def ollama(profile, credentials):
        # Lazy imports keep provider-specific dependencies out of unrelated jobs.
        from .ollama import OllamaBackend
        return OllamaBackend(profile.model, base_url=profile.options.get("base_url", "http://localhost:11434"))

    def openai(profile, credentials):
        from .openai import OpenAIBackend
        from .auth import ApiKeyAuth
        return OpenAIBackend(
            profile.model,
            base_url=profile.options.get("base_url", "https://api.openai.com/v1"),
            credential_store=credentials,
            auth=ApiKeyAuth(profile.credential_ref or ""),
        )

    def gemini(profile, credentials):
        from .gemini import GeminiBackend
        from .auth import ApiKeyAuth, OAuthTokenAuth
        if profile.auth_type == "oauth":
            from .oauth import GeminiOAuth
            auth = OAuthTokenAuth(GeminiOAuth(
                credential_ref=profile.credential_ref or "",
                store=credentials,
                client_id=profile.options.get("oauth_client_id"),
            ))
        else:
            auth = ApiKeyAuth(profile.credential_ref or "")
        return GeminiBackend(
            profile.model,
            base_url=profile.options.get("base_url", "https://generativelanguage.googleapis.com/v1beta"),
            credential_store=credentials,
            auth=auth,
        )

    def claude(profile, credentials):
        from .claude import ClaudeBackend
        from .auth import ApiKeyAuth
        return ClaudeBackend(
            profile.model,
            base_url=profile.options.get("base_url", "https://api.anthropic.com"),
            credential_store=credentials,
            auth=ApiKeyAuth(profile.credential_ref or ""),
        )

    registry.register(ProviderDescriptor("ollama", "Ollama", ollama, model_discovery_supported=True))
    registry.register(ProviderDescriptor(
        "openai", "OpenAI API", openai, auth_methods=("api_key",),
        configuration_supported=True, model_discovery_supported=True,
    ))
    registry.register(ProviderDescriptor(
        "gemini", "Gemini API", gemini, auth_methods=("api_key", "oauth"),
        configuration_supported=True, login_supported=True, model_discovery_supported=True,
    ))
    registry.register(ProviderDescriptor(
        "claude", "Claude API", claude, auth_methods=("api_key",),
        configuration_supported=True, model_discovery_supported=True,
    ))
    return registry
