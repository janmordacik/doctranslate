"""Data contracts shared by document adapters and translation backends."""

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SourceMetadata:
    """Immutable metadata needed to reproduce document formatting."""

    source_path: str
    media_type: str
    source_language: str
    target_language: str
    page_count: int | None = None
    title: str | None = None
    layout_revision: int = 1
    attributes: Mapping[str, Any] = field(default_factory=dict)
    source_sha256: str | None = None
    resources: Sequence["ResourceReference"] = field(default_factory=tuple)
    extensions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceReference:
    """Portable resource reference used by format adapters."""

    resource_id: str
    role: str
    media_type: str
    path: str
    sha256: str | None = None


@dataclass(frozen=True)
class XhtmlBlock:
    """One ordered translatable XHTML block with source layout metadata."""

    block_id: str
    page_number: int
    order: int
    text: str
    markup: str = ""
    bbox: tuple[float, float, float, float] | None = None
    style: Mapping[str, Any] = field(default_factory=dict)
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def translated(self, text: str, markup: str | None = None) -> "XhtmlBlock":
        """Return a copy with translated text while preserving source layout."""
        return replace(self, text=text, markup=self.markup if markup is None else markup)


@dataclass(frozen=True)
class XhtmlDocument:
    """Ordered XHTML interchange document plus input-file metadata."""

    metadata: SourceMetadata
    blocks: Sequence[XhtmlBlock]
    html: str = ""
    schema: int = 1

    def __post_init__(self) -> None:
        block_ids = [block.block_id for block in self.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("XHTML block identifiers must be unique")
        if any(block.page_number < 1 for block in self.blocks):
            raise ValueError("XHTML block page numbers must be positive")

    def with_blocks(self, blocks: Sequence[XhtmlBlock]) -> "XhtmlDocument":
        """Return a document with replacement blocks and unchanged metadata."""
        return replace(self, blocks=tuple(blocks))

    def block_map(self) -> dict[str, XhtmlBlock]:
        """Return a defensive mapping of the immutable block view."""
        return {block.block_id: block for block in self.blocks}
