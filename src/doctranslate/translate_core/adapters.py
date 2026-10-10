"""Plugin protocols and registry for document formats and translation services."""

from pathlib import Path
from typing import Generic, Protocol, Sequence, TypeVar

from .contracts import XhtmlDocument


class DocumentInputAdapter(Protocol):
    """Read a source format and expose it as an XHTML document."""

    media_type: str

    def read(self, source: Path) -> XhtmlDocument:
        """Read source and return the format-neutral document model."""
        ...


class DocumentOutputAdapter(Protocol):
    """Render an XHTML document into a target format."""

    media_type: str

    def write(self, document: XhtmlDocument, target: Path) -> Path:
        """Render document to target and return the resulting path."""
        ...


class TranslationBackend(Protocol):
    """Translate ordered text values without knowing the source file format."""

    name: str

    def translate(
        self,
        texts: Sequence[str],
        *,
        source_language: str,
        target_language: str,
    ) -> Sequence[str]:
        """Translate texts while preserving their order and cardinality."""
        ...


T = TypeVar("T")


class AdapterRegistry(Generic[T]):
    """Small explicit registry used to select format plugins by media type."""

    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def register(self, media_type: str, adapter: T) -> None:
        """Register or replace an adapter for a media type."""
        key = media_type.strip().lower()
        if not key:
            raise ValueError("media_type must not be empty")
        self._items[key] = adapter

    def get(self, media_type: str) -> T:
        """Return a registered adapter or raise a descriptive error."""
        key = media_type.strip().lower()
        try:
            return self._items[key]
        except KeyError as exc:
            available = ", ".join(sorted(self._items)) or "(none)"
            raise LookupError(f"No adapter for {media_type!r}; available: {available}") from exc

    def media_types(self) -> tuple[str, ...]:
        """Return registered media types in stable order."""
        return tuple(sorted(self._items))
