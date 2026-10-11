"""Bridge legacy page groups to the canonical XHTML translation model."""

from __future__ import annotations

from copy import deepcopy
import html
import re
from typing import Any, Callable, Mapping, Sequence

from doctranslate.ai.contracts import SegmentRequest, SegmentResult
from doctranslate.translation.basic import BatchExecutor
from doctranslate.translation.contracts import (
    TranslationContext,
    TranslationError,
    TranslationOptions,
)
from doctranslate.translate_core.contracts import (
    ResourceReference,
    SourceMetadata,
    XhtmlBlock,
    XhtmlDocument,
)


class TranslationBridgeError(TranslationError):
    """Raised when a legacy block mapping cannot be proven lossless."""


def _block_id(page_number: int, order: int) -> str:
    """Match the stable ID convention used by the current legacy extractor."""
    return f"p{page_number + 1:06d}_b{order + 1:04d}"


def _plain_text(markup: str) -> str:
    """Extract a conservative text view without modifying source markup."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        numbers = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise TranslationBridgeError(
            "invalid_geometry",
            f"Legacy block geometry is not numeric: {value!r}",
        ) from exc
    if len(numbers) != 4:
        raise TranslationBridgeError(
            "invalid_geometry",
            f"Legacy block geometry needs four coordinates: {value!r}",
        )
    return numbers  # type: ignore[return-value]


def _source_metadata(metadata: Mapping[str, Any]) -> SourceMetadata:
    """Convert legacy metadata while retaining the complete source mapping."""
    resources = []
    for item in metadata.get("resources", ()):
        if not isinstance(item, Mapping):
            raise TranslationBridgeError("invalid_resource", "Legacy resource is not an object")
        try:
            resources.append(
                ResourceReference(
                    resource_id=str(item["resource_id"]),
                    role=str(item["role"]),
                    media_type=str(item["media_type"]),
                    path=str(item["path"]),
                    sha256=item.get("sha256"),
                )
            )
        except KeyError as exc:
            raise TranslationBridgeError(
                "invalid_resource",
                f"Legacy resource is missing {exc.args[0]}",
            ) from exc
    return SourceMetadata(
        source_path=str(metadata.get("input", metadata.get("source_path", ""))),
        media_type=str(metadata.get("media_type", "application/pdf")),
        source_language=str(metadata.get("inlang", metadata.get("source_language", ""))),
        target_language=str(metadata.get("outlang", metadata.get("target_language", ""))),
        page_count=metadata.get("last_page", metadata.get("page_count")),
        title=metadata.get("title"),
        layout_revision=int(metadata.get("layout_revision", 1)),
        attributes=deepcopy(dict(metadata)),
        source_sha256=metadata.get("source_hash", metadata.get("source_sha256")),
        resources=tuple(resources),
        extensions={"bridge": "legacy-page-groups-v1"},
    )


def legacy_groups_to_document(
    metadata: Mapping[str, Any],
    groups: Sequence[tuple[int, Sequence[Mapping[str, Any]]]],
    translations: Mapping[str, str] | None = None,
) -> XhtmlDocument:
    """Create XHTML blocks while retaining page, geometry and legacy metadata."""
    translations = translations or {}
    blocks: list[XhtmlBlock] = []
    for page_number, page_blocks in groups:
        for order, legacy in enumerate(page_blocks):
            if not isinstance(legacy, Mapping):
                raise TranslationBridgeError(
                    "invalid_block",
                    f"Legacy block {page_number}/{order} is not an object",
                )
            ident = str(legacy.get("block_id", _block_id(page_number, order)))
            markup = str(
                translations.get(
                    ident,
                    legacy.get("markup", legacy.get("html", "")),
                )
            )
            raw_style = legacy.get("styles", legacy.get("style", {}))
            style = deepcopy(dict(raw_style)) if isinstance(raw_style, Mapping) else {}
            attributes = {
                "legacy": deepcopy(dict(legacy)),
                "rotation": legacy.get("rotation"),
                "row_layout": deepcopy(legacy.get("row_layout", [])),
            }
            text = _plain_text(markup) if ident in translations else str(legacy.get("text", _plain_text(markup)))
            blocks.append(
                XhtmlBlock(
                    block_id=ident,
                    page_number=page_number + 1,
                    order=order,
                    text=text,
                    markup=markup,
                    bbox=_bbox(legacy.get("bbox", legacy.get("rect"))),
                    style=style,
                    attributes=attributes,
                )
            )
    try:
        return XhtmlDocument(_source_metadata(metadata), tuple(blocks))
    except (TypeError, ValueError) as exc:
        raise TranslationBridgeError(
            "invalid_document",
            f"Legacy groups cannot form a canonical document: {exc}",
        ) from exc


def document_to_legacy_groups(
    document: XhtmlDocument,
    groups: Sequence[tuple[int, Sequence[Mapping[str, Any]]]],
) -> list[tuple[int, list[dict[str, Any]]]]:
    """Apply translated markup to a copy while preserving all legacy layout keys."""
    expected: list[str] = []
    result: list[tuple[int, list[dict[str, Any]]]] = []
    for page_number, page_blocks in groups:
        converted: list[dict[str, Any]] = []
        for order, legacy in enumerate(page_blocks):
            ident = str(legacy.get("block_id", _block_id(page_number, order)))
            expected.append(ident)
            converted.append(deepcopy(dict(legacy)))
        result.append((page_number, converted))

    actual = [block.block_id for block in document.blocks]
    if actual != expected:
        raise TranslationBridgeError(
            "mapping_mismatch",
            "Canonical XHTML blocks do not match legacy page-group IDs or order",
        )
    by_id = document.block_map()
    for page_number, page_blocks in result:
        for order, legacy in enumerate(page_blocks):
            ident = str(legacy.get("block_id", _block_id(page_number, order)))
            block = by_id[ident]
            legacy["markup"] = block.markup
            legacy["text"] = block.text
    return result


class LegacyBatchAdapter(BatchExecutor):
    """Adapt the existing prompt/batch callable without importing translate.py."""

    def __init__(
        self,
        execute_batch: Callable[
            [Sequence[SegmentRequest], TranslationOptions, TranslationContext],
            Sequence[SegmentResult],
        ],
    ) -> None:
        self.execute_batch = execute_batch

    def execute(
        self,
        requests: Sequence[SegmentRequest],
        options: TranslationOptions,
        *,
        context: TranslationContext,
    ) -> Sequence[SegmentResult]:
        """Delegate unchanged requests and options to the legacy composition root."""
        return self.execute_batch(requests, options, context)
