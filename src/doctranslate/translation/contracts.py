"""Provider- and format-neutral translation engine contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Mapping, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from doctranslate.translate_core.contracts import XhtmlDocument


def normalize_language(value: str) -> str:
    """Return a canonical language tag and reject empty language values."""
    if not isinstance(value, str):
        raise ValueError("language must be a string")
    normalized = value.strip().lower().replace("_", "-")
    if not normalized:
        raise ValueError("language must not be empty")
    return normalized


class TranslationError(RuntimeError):
    """Typed failure crossing the translation-engine boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        checkpoint_reference: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.checkpoint_reference = checkpoint_reference

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class TranslationCancelled(TranslationError):
    """Raised when a caller cancels an engine run."""

    def __init__(self, message: str = "Translation was cancelled") -> None:
        super().__init__("cancelled", message, retryable=False)


@dataclass(frozen=True)
class TranslationOptions:
    """Effective options shared by engines and included in cache identity."""

    source_language: str
    target_language: str
    target_variant: str = "auto"
    translator_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source = normalize_language(self.source_language)
        target = normalize_language(self.target_language)
        if not isinstance(self.target_variant, str):
            raise ValueError("target_variant must be a string")
        variant = self.target_variant.strip() or "auto"
        if not isinstance(self.translator_options, Mapping):
            raise ValueError("translator_options must be a mapping")
        object.__setattr__(self, "source_language", source)
        object.__setattr__(self, "target_language", target)
        object.__setattr__(self, "target_variant", variant)
        object.__setattr__(self, "translator_options", dict(self.translator_options))

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "TranslationOptions":
        """Create options from a JSON-like map and reject missing languages."""
        try:
            source = values["source_language"]
            target = values["target_language"]
        except KeyError as exc:
            raise ValueError(f"missing translation option: {exc.args[0]}") from exc
        return cls(
            source_language=source,
            target_language=target,
            target_variant=values.get("target_variant", "auto"),
            translator_options=values.get("translator_options", {}),
        )

    def effective_mapping(self) -> dict[str, Any]:
        """Return a defensive JSON-like mapping for identity and diagnostics."""
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "target_variant": self.target_variant,
            "translator_options": dict(self.translator_options),
        }


@dataclass(frozen=True)
class TranslationContext:
    """Runtime controls injected by the worker, without GUI or queue coupling."""

    cancel_event: Any = None
    on_progress: Callable[..., None] | None = None
    on_preview: Callable[..., None] | None = None
    on_batch_committed: Callable[..., None] | None = None
    checkpoint: Any = None
    logger: Callable[..., None] | None = None
    clock: Callable[[], float] = time.monotonic


@dataclass(frozen=True)
class TranslationMetrics:
    """Measured or estimated counters returned with a translated document."""

    translator_id: str
    translator_revision: str
    batches: int = 0
    segments: int = 0
    resumed: int = 0
    ai_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    token_accounting: Mapping[str, str] = field(default_factory=dict)
    timings: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "batches",
            "segments",
            "resumed",
            "ai_calls",
            "tool_calls",
            "prompt_tokens",
            "output_tokens",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        object.__setattr__(self, "token_accounting", dict(self.token_accounting))
        object.__setattr__(self, "timings", dict(self.timings))


@dataclass(frozen=True)
class TranslationResult:
    """Successful engine result containing a complete XHTML document."""

    document: "XhtmlDocument"
    metrics: TranslationMetrics
    warnings: tuple[str, ...] = ()


class TranslationEngine(Protocol):
    """Common public contract for basic and advanced translation strategies."""

    def translate(
        self,
        document: "XhtmlDocument",
        options: TranslationOptions,
        *,
        context: TranslationContext | None = None,
    ) -> TranslationResult:
        """Translate the document while preserving XHTML structure and metadata."""
        ...


@dataclass(frozen=True)
class EngineDescriptor:
    """Explicit registry entry and its injected constructor."""

    id: str
    label: str
    revision: str
    options_schema: Mapping[str, type | tuple[type, ...]] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()
    available: bool = True
    reason: str = ""
    factory: Callable[[Any, TranslationOptions], TranslationEngine] | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("engine id must not be empty")
        if not self.label.strip():
            raise ValueError("engine label must not be empty")
        if not self.revision.strip():
            raise ValueError("engine revision must not be empty")
        if self.available and self.factory is None:
            raise ValueError("available engine needs a factory")
        object.__setattr__(self, "options_schema", dict(self.options_schema))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))


@dataclass(frozen=True)
class TranslatorSelection:
    """Persistable per-job module choice, independent of provider and model."""

    translator_id: str = "basic"
    translator_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.translator_id.strip():
            raise ValueError("translator_id must not be empty")
        object.__setattr__(self, "translator_options", dict(self.translator_options))
