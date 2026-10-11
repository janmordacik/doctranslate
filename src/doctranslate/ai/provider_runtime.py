"""Shared provider configuration, credential resolution and smoke probes."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .auth import (
    CredentialStore,
    CredentialStoreUnavailable,
    EnvCredentialStore,
    KeyringCredentialStore,
)
from .contracts import ProbeResult
from .profiles import AiProfile, ProfileStore
from .registry import ProviderRegistry, build_default_provider_registry


@dataclass(frozen=True)
class CredentialStorageStatus:
    """Safe diagnostic result for GUI and CLI credential-store checks."""

    available: bool
    writable: bool
    backend: str
    message: str
    remedy: str


class ChainedCredentialStore:
    """Read keyring first and explicit environment references second."""

    def __init__(self, primary: CredentialStore | None = None) -> None:
        self.primary = primary
        self.environment = EnvCredentialStore()

    def get(self, reference: str) -> str | None:
        if reference.startswith("env:"):
            return self.environment.get(reference)
        if self.primary is None:
            return None
        return self.primary.get(reference)

    def set(self, reference: str, secret: str) -> None:
        if self.primary is None:
            raise CredentialStoreUnavailable(
                "Secure credential storage is unavailable.",
                remedy=KeyringCredentialStore.INSTALL_REMEDY,
            )
        self.primary.set(reference, secret)

    def delete(self, reference: str) -> None:
        if reference.startswith("env:"):
            raise CredentialStoreUnavailable(
                "Environment credentials are read-only.",
                remedy="Use the environment variable configured by the credential reference.",
            )
        if self.primary is not None:
            self.primary.delete(reference)


def credential_store_for(profile: AiProfile | None = None) -> CredentialStore:
    """Resolve credentials exactly as the worker and GUI do, without plaintext fallback."""
    if profile is not None and profile.credential_ref and profile.credential_ref.startswith("env:"):
        return EnvCredentialStore()
    try:
        return ChainedCredentialStore(KeyringCredentialStore())
    except CredentialStoreUnavailable:
        return ChainedCredentialStore()


def credential_storage_status() -> CredentialStorageStatus:
    """Check secure storage without opening a browser or contacting a provider."""
    try:
        store = KeyringCredentialStore()
    except CredentialStoreUnavailable as exc:
        return CredentialStorageStatus(
            available=False,
            writable=False,
            backend="unavailable",
            message=str(exc),
            remedy=exc.remedy,
        )
    backend = type(getattr(store, "_keyring", object())).__name__
    return CredentialStorageStatus(
        available=True,
        writable=True,
        backend=f"keyring:{backend}",
        message="Secure credential storage is available.",
        remedy="",
    )


def save_profile_configuration(
    profile: AiProfile,
    profile_store: ProfileStore,
    credential_store: CredentialStore,
    *,
    model: str,
    credential_ref: str | None,
    api_key: str | None = None,
    base_url: str | None = None,
    oauth_client_id: str | None = None,
) -> AiProfile:
    """Persist a new non-secret profile revision and optionally store an API key."""
    model = model.strip()
    if not model:
        raise ValueError("model is required")
    reference = (credential_ref or "").strip() or None
    if api_key and api_key.strip():
        reference = reference or f"keyring:{profile.provider_id}:{profile.profile_id}"
        credential_store.set(reference, api_key.strip())
    if profile.provider_id != "ollama" and not reference:
        raise ValueError("credential reference or API key is required")
    options = dict(profile.options)
    if base_url is not None:
        options["base_url"] = base_url.strip()
    if oauth_client_id is not None:
        options["oauth_client_id"] = oauth_client_id.strip()
    updated = replace(
        profile,
        revision=profile.revision + 1,
        model=model,
        auth_type="none" if profile.provider_id == "ollama" else "api_key",
        credential_ref=reference,
        options=options,
    )
    return profile_store.save(updated)


def provider_backend(profile: AiProfile, credentials: CredentialStore | None = None, registry: ProviderRegistry | None = None):
    """Create the same backend used by translation and GUI diagnostics."""
    return (registry or build_default_provider_registry()).create(
        profile, credentials or credential_store_for(profile)
    )


def probe_profile(profile: AiProfile, credentials: CredentialStore | None = None) -> ProbeResult:
    """Run a cheap endpoint/auth/model probe; it never sends document text."""
    backend = provider_backend(profile, credentials)
    probe = getattr(backend, "probe", None)
    if not callable(probe):
        return ProbeResult(profile.provider_id, profile.model, "probe_unsupported", message="Provider has no smoke probe.")
    return probe()


def discover_profile_models(profile: AiProfile, credentials: CredentialStore | None = None) -> tuple[str, ...]:
    """Return provider model IDs using the same credential resolver as translation."""
    backend = provider_backend(profile, credentials)
    discover = getattr(backend, "list_models", None)
    if not callable(discover):
        return ()
    return tuple(discover())

