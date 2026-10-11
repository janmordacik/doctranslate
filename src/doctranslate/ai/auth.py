"""Authentication boundaries with no plaintext-secret persistence fallback."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol


class CredentialStore(Protocol):
    """Secret storage boundary; implementations must never expose secrets in logs."""

    def get(self, reference: str) -> str | None:
        """Resolve a non-secret reference to a secret, if available."""
        ...

    def set(self, reference: str, secret: str) -> None:
        """Store a secret under a non-secret reference."""
        ...

    def delete(self, reference: str) -> None:
        """Remove a stored secret without failing if it is absent."""
        ...


class MemoryCredentialStore:
    """Deterministic store for tests and short-lived interactive sessions."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, reference: str) -> str | None:
        return self._values.get(reference)

    def set(self, reference: str, secret: str) -> None:
        if not reference or not secret:
            raise ValueError("credential reference and secret are required")
        self._values[reference] = secret

    def delete(self, reference: str) -> None:
        self._values.pop(reference, None)


class EnvCredentialStore:
    """Resolve explicit env references; never writes environment values to disk."""

    def get(self, reference: str) -> str | None:
        if not reference.startswith("env:"):
            return None
        return os.environ.get(reference[4:])

    def set(self, reference: str, secret: str) -> None:
        raise RuntimeError("Environment credential references are read-only")

    def delete(self, reference: str) -> None:
        raise RuntimeError("Environment credential references are read-only")


class KeyringCredentialStore:
    """Use the optional OS keyring package; never fall back to plaintext files."""

    def __init__(self, service: str = "doctranslate") -> None:
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError(
                "Secure credential storage requires the optional keyring dependency"
            ) from exc
        self._keyring = keyring
        self.service = service

    def get(self, reference: str) -> str | None:
        return self._keyring.get_password(self.service, reference)

    def set(self, reference: str, secret: str) -> None:
        if not reference or not secret:
            raise ValueError("credential reference and secret are required")
        self._keyring.set_password(self.service, reference, secret)

    def delete(self, reference: str) -> None:
        try:
            self._keyring.delete_password(self.service, reference)
        except Exception:
            pass


@dataclass(frozen=True)
class ApiKeyAuth:
    """Resolve an API key only at request time from the configured store."""

    credential_ref: str

    def resolve(self, store: CredentialStore) -> str:
        secret = store.get(self.credential_ref)
        if not secret:
            raise RuntimeError(
                f"Credential is unavailable for {self.credential_ref!r}; configure the provider"
            )
        return secret


class OAuthAuth(Protocol):
    """Provider-neutral boundary for interactive login and token refresh."""

    def login(self, interactive: bool = True) -> None:
        """Start an interactive or explicitly non-interactive login flow."""
        ...

    def token(self, interactive: bool = False) -> str:
        """Return a valid access token, optionally prompting for login."""
        ...

    def logout(self) -> None:
        """Discard locally stored OAuth tokens."""
        ...



@dataclass(frozen=True)
class OAuthTokenAuth:
    """Resolve a bearer token at request time without persisting it in a profile."""

    oauth: OAuthAuth

    def resolve(self, _store: CredentialStore) -> str:
        token = self.oauth.token(interactive=False)
        if not token:
            raise RuntimeError("OAuth login is required for this provider")
        return token
def redact_secrets(value: object, secrets: tuple[str, ...] = ()) -> object:
    """Recursively redact known credentials before diagnostic serialization."""
    if isinstance(value, str):
        result = value
        for secret in secrets:
            if secret:
                result = result.replace(secret, "***")
        return result
    if isinstance(value, dict):
        return {str(key): redact_secrets(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item, secrets) for item in value)
    return value
