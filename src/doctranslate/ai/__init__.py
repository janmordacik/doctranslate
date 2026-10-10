"""Provider-neutral AI contracts, profiles and authentication boundaries."""

from .contracts import (
    AiBackend,
    BackendError,
    SegmentRequest,
    SegmentResult,
)
from .auth import (
    ApiKeyAuth,
    CredentialStore,
    EnvCredentialStore,
    MemoryCredentialStore,
    KeyringCredentialStore,
    OAuthAuth,
    redact_secrets,
)
from .profiles import AiProfile, ProfileError, ProfileStore
from .translation import Prompt, PromptBuilder, SegmentTranslationPipeline, translate_text
from .registry import ProviderDescriptor, ProviderRegistry, build_default_provider_registry
from .oauth import BrowserOAuth, GeminiOAuth, OAuthTokens

__all__ = [
    "AiBackend",
    "AiProfile",
    "ApiKeyAuth",
    "BackendError",
    "CredentialStore",
    "EnvCredentialStore",
    "MemoryCredentialStore",
    "KeyringCredentialStore",
    "OAuthAuth",
    "ProfileError",
    "ProfileStore",
    "SegmentRequest",
    "SegmentResult",
    "redact_secrets",
    "Prompt",
    "PromptBuilder",
    "SegmentTranslationPipeline",
    "translate_text",
    "ProviderDescriptor",
    "ProviderRegistry",
    "build_default_provider_registry",
    "BrowserOAuth",
    "GeminiOAuth",
    "OAuthTokens",
]
