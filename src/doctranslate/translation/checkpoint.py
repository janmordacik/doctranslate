"""Versioned, atomic checkpoint storage for translation engines."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .contracts import TranslationError, TranslationOptions


CHECKPOINT_SCHEMA = 1
CHECKPOINT_REVISION = "translation-checkpoint-v1"
AtomicWriter = Callable[[Path, str], None]


class CheckpointError(TranslationError):
    """Typed failure while reading, validating or persisting a checkpoint."""


def canonical_identity(
    *,
    source: Mapping[str, Any] | str,
    translator_id: str,
    translator_revision: str,
    options: TranslationOptions | Mapping[str, Any],
    provider_id: str | None = None,
    profile_id: str | None = None,
    model: str | None = None,
    style_revision: str | None = None,
    prompt_revision: str | None = None,
    segment_policy: str | None = None,
) -> str:
    """Hash all state that can make a translated segment incompatible."""
    if isinstance(options, TranslationOptions):
        effective_options = options.effective_mapping()
    else:
        effective_options = dict(options)
    payload = {
        "source": source if isinstance(source, str) else dict(source),
        "translator_id": translator_id,
        "translator_revision": translator_revision,
        "provider_id": provider_id,
        "profile_id": profile_id,
        "model": model,
        "style_revision": style_revision,
        "prompt_revision": prompt_revision,
        "segment_policy": segment_policy,
        "options": effective_options,
    }
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CheckpointError(
            "invalid_identity",
            f"Checkpoint identity is not JSON serializable: {exc}",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ValidatedSegment:
    """One accepted translation and its source/provenance evidence."""

    segment_id: str
    source_text: str
    text: str
    source_markup: str = ""
    markup: str = ""
    term_bindings: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("segment_id", "source_text", "text", "source_markup", "markup"):
            if not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be a string")
        if not self.segment_id:
            raise ValueError("segment_id must not be empty")
        object.__setattr__(self, "term_bindings", tuple(self.term_bindings))
        object.__setattr__(self, "provenance", dict(self.provenance))

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the segment without provider-specific objects."""
        return {
            "segment_id": self.segment_id,
            "source_text": self.source_text,
            "text": self.text,
            "source_markup": self.source_markup,
            "markup": self.markup,
            "term_bindings": list(self.term_bindings),
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidatedSegment":
        """Validate and deserialize one persisted segment."""
        try:
            return cls(
                segment_id=value["segment_id"],
                source_text=value["source_text"],
                text=value["text"],
                source_markup=value.get("source_markup", ""),
                markup=value.get("markup", ""),
                term_bindings=tuple(value.get("term_bindings", ())),
                provenance=value.get("provenance", {}),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CheckpointError(
                "invalid_segment",
                f"Invalid validated segment: {exc}",
            ) from exc


@dataclass(frozen=True)
class CheckpointState:
    """Validated persisted state that can safely be used for resume."""

    identity: str
    validated_segments: tuple[ValidatedSegment, ...] = ()
    used_memory_revision: str | None = None
    counters: Mapping[str, int] = field(default_factory=dict)
    dirty_ids: tuple[str, ...] = ()
    schema: int = CHECKPOINT_SCHEMA
    revision: str = CHECKPOINT_REVISION

    def __post_init__(self) -> None:
        if self.schema != CHECKPOINT_SCHEMA:
            raise ValueError(f"unsupported checkpoint schema: {self.schema}")
        if not self.identity:
            raise ValueError("checkpoint identity must not be empty")
        ids = [segment.segment_id for segment in self.validated_segments]
        if len(ids) != len(set(ids)):
            raise ValueError("checkpoint segment IDs must be unique")
        if any(type(value) is not int or value < 0 for value in self.counters.values()):
            raise ValueError("checkpoint counters must be non-negative integers")
        object.__setattr__(self, "validated_segments", tuple(self.validated_segments))
        object.__setattr__(self, "counters", dict(self.counters))
        object.__setattr__(self, "dirty_ids", tuple(self.dirty_ids))

    def to_mapping(self) -> dict[str, Any]:
        """Serialize state in a stable, JSON-compatible structure."""
        return {
            "schema": self.schema,
            "revision": self.revision,
            "identity": self.identity,
            "validated_segments": [
                segment.to_mapping() for segment in self.validated_segments
            ],
            "used_memory_revision": self.used_memory_revision,
            "counters": dict(self.counters),
            "dirty_ids": list(self.dirty_ids),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CheckpointState":
        """Reject malformed or unsupported state before it reaches an engine."""
        if not isinstance(value, Mapping):
            raise CheckpointError("invalid_schema", "Checkpoint root must be an object")
        if value.get("schema") != CHECKPOINT_SCHEMA:
            raise CheckpointError(
                "invalid_schema",
                f"Unsupported checkpoint schema: {value.get('schema')!r}",
            )
        try:
            segments = tuple(
                ValidatedSegment.from_mapping(item)
                for item in value.get("validated_segments", ())
            )
            return cls(
                identity=value["identity"],
                validated_segments=segments,
                used_memory_revision=value.get("used_memory_revision"),
                counters=value.get("counters", {}),
                dirty_ids=tuple(value.get("dirty_ids", ())),
                schema=value["schema"],
                revision=value.get("revision", CHECKPOINT_REVISION),
            )
        except CheckpointError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise CheckpointError(
                "invalid_schema",
                f"Invalid checkpoint state: {exc}",
            ) from exc


def _atomic_write(path: Path, text: str) -> None:
    """Write a temporary sibling and replace only after the full write succeeds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


class CheckpointStore(Protocol):
    """Storage contract allowing tests and composition roots to inject writers."""

    def load(self, expected_identity: str | None = None) -> CheckpointState | None:
        """Load and validate a checkpoint, or return None when it does not exist."""
        ...

    def save(self, state: CheckpointState) -> Path:
        """Atomically persist a validated checkpoint."""
        ...


class JsonCheckpointStore:
    """Versioned JSON implementation with an injectable atomic writer."""

    def __init__(
        self,
        path: Path,
        *,
        atomic_writer: AtomicWriter = _atomic_write,
    ) -> None:
        self.path = Path(path)
        self.atomic_writer = atomic_writer

    def load(self, expected_identity: str | None = None) -> CheckpointState | None:
        """Read one checkpoint and reject mismatch instead of silently resuming."""
        if not self.path.is_file():
            return None
        try:
            raw = self.path.read_text(encoding="utf-8")
            state = CheckpointState.from_mapping(json.loads(raw))
        except CheckpointError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointError(
                "invalid_schema",
                f"Cannot read checkpoint {self.path}: {exc}",
            ) from exc
        if expected_identity is not None and state.identity != expected_identity:
            raise CheckpointError(
                "identity_mismatch",
                "Checkpoint identity does not match the current translation inputs",
                checkpoint_reference=str(self.path),
            )
        return state

    def save(self, state: CheckpointState) -> Path:
        """Validate before writing; a failed write leaves the old file untouched."""
        try:
            payload = json.dumps(
                state.to_mapping(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ) + "\n"
            self.atomic_writer(self.path, payload)
        except CheckpointError:
            raise
        except (OSError, TypeError, ValueError) as exc:
            raise CheckpointError(
                "storage_error",
                f"Cannot save checkpoint {self.path}: {exc}",
                checkpoint_reference=str(self.path),
            ) from exc
        return self.path
