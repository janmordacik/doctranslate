"""Format-neutral translation engine contracts and explicit registry."""

from .contracts import (
    EngineDescriptor,
    TranslationContext,
    TranslationEngine,
    TranslationError,
    TranslationMetrics,
    TranslationOptions,
    TranslationResult,
    TranslationCancelled,
    TranslatorSelection,
)
from .registry import TranslationEngineRegistry, TranslationRegistryError
from .basic import BasicTranslationEngine, BatchExecutor

__all__ = [
    "EngineDescriptor",
    "TranslationContext",
    "TranslationEngine",
    "TranslationEngineRegistry",
    "TranslationError",
    "TranslationMetrics",
    "TranslationOptions",
    "TranslationRegistryError",
    "TranslationResult",
    "TranslationCancelled",
    "TranslatorSelection",
    "BasicTranslationEngine",
    "BatchExecutor",
]
