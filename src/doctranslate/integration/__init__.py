"""Integration boundaries between legacy I/O and the translation core."""

from .translation_bridge import (
    LegacyBatchAdapter,
    TranslationBridgeError,
    document_to_legacy_groups,
    legacy_groups_to_document,
)

__all__ = [
    "LegacyBatchAdapter",
    "TranslationBridgeError",
    "document_to_legacy_groups",
    "legacy_groups_to_document",
]
