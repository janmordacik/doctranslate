"""Provider-neutral AI contracts, profiles and authentication boundaries."""

from .contracts import (
    AiBackend,
    BackendError,
    SegmentRequest,
    ProbeResult,
    SegmentResult,
)
from .auth import (
    ApiKeyAuth,
    CredentialStore,
    CredentialStoreUnavailable,
    EnvCredentialStore,
    MemoryCredentialStore,
    OAuthTokenAuth,
    KeyringCredentialStore,
    OAuthAuth,
    redact_secrets,
)
from .profiles import AiProfile, ProfileError, ProfileStore
from .styles import (
    StyleError,
    StyleLibrary,
    StylePolicy,
    StyleProfile,
    StylePromptRules,
    compose_policy,
)
from .benchmark_fixtures import (
    BenchmarkFixture,
    BenchmarkFixtureError,
    load_builtin_fixtures,
)
from .benchmark import BenchmarkResult, BenchmarkRunner, BenchmarkSample
from .translation import (
    Prompt,
    PromptBuilder,
    SegmentTranslationPipeline,
    translate_prompt,
    translate_text,
)
from .registry import ProviderDescriptor, ProviderRegistry, build_default_provider_registry
from .provider_runtime import (
    ChainedCredentialStore,
    CredentialStorageStatus,
    credential_store_for,
    credential_storage_status,
    discover_profile_models,
    probe_profile,
    provider_backend,
    save_profile_configuration,
)
from .oauth import (
    BrowserOAuth,
    GeminiOAuth,
    OAuthConfigurationError,
    OAuthTokens,
    resolve_gemini_oauth_client_id,
)

__all__ = [
    "ProbeResult",
    "ChainedCredentialStore",
    "CredentialStoreUnavailable",
    "CredentialStorageStatus",
    "credential_store_for",
    "credential_storage_status",
    "discover_profile_models",
    "probe_profile",
    "provider_backend",
    "save_profile_configuration",
    "AiBackend",
    "OAuthTokenAuth",
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
    "StyleError",
    "StyleLibrary",
    "StylePolicy",
    "StyleProfile",
    "StylePromptRules",
    "compose_policy",
    "BenchmarkFixture",
    "BenchmarkFixtureError",
    "load_builtin_fixtures",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkSample",
    "SegmentRequest",
    "SegmentResult",
    "redact_secrets",
    "Prompt",
    "PromptBuilder",
    "SegmentTranslationPipeline",
    "translate_text",
    "translate_prompt",
    "ProviderDescriptor",
    "ProviderRegistry",
    "build_default_provider_registry",
    "BrowserOAuth",
    "GeminiOAuth",
    "OAuthConfigurationError",
    "OAuthTokens",
    "resolve_gemini_oauth_client_id",
]
