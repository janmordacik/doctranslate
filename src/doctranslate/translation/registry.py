"""Explicit registry for format-neutral translation engines."""

from __future__ import annotations

import json
from typing import Any

from .contracts import (
    EngineDescriptor,
    TranslationEngine,
    TranslationError,
    TranslationOptions,
)


class TranslationRegistryError(TranslationError):
    """Typed error for unknown, duplicate or unavailable engine selections."""


class TranslationEngineRegistry:
    """Register and construct engines without dynamic plugin discovery."""

    def __init__(self) -> None:
        self._items: dict[str, EngineDescriptor] = {}

    def register(self, descriptor: EngineDescriptor) -> None:
        """Register one explicit descriptor and reject duplicate IDs."""
        engine_id = descriptor.id.strip().lower()
        if engine_id in self._items:
            raise TranslationRegistryError(
                "duplicate_engine",
                f"Translation engine ID is already registered: {descriptor.id}",
            )
        if engine_id != descriptor.id:
            descriptor = EngineDescriptor(
                id=engine_id,
                label=descriptor.label,
                revision=descriptor.revision,
                options_schema=descriptor.options_schema,
                capabilities=descriptor.capabilities,
                available=descriptor.available,
                reason=descriptor.reason,
                factory=descriptor.factory,
            )
        self._items[engine_id] = descriptor

    def list(self) -> tuple[EngineDescriptor, ...]:
        """Return stable descriptors without constructing any engine."""
        return tuple(self._items[key] for key in sorted(self._items))

    def get(self, engine_id: str) -> EngineDescriptor:
        """Return a descriptor or a typed unknown-engine error."""
        key = engine_id.strip().lower()
        try:
            return self._items[key]
        except KeyError as exc:
            available = ", ".join(item.id for item in self.list()) or "(none)"
            raise TranslationRegistryError(
                "unknown_engine",
                f"Unknown translation engine {engine_id!r}; available: {available}",
            ) from exc

    def validate_options(
        self,
        descriptor: EngineDescriptor,
        options: TranslationOptions,
    ) -> None:
        """Reject unknown or incorrectly typed engine-specific options."""
        if not isinstance(options, TranslationOptions):
            raise TranslationRegistryError(
                "invalid_options",
                "Translation engine options must be TranslationOptions",
            )
        try:
            json.dumps(options.translator_options)
        except (TypeError, ValueError) as exc:
            raise TranslationRegistryError(
                "invalid_options",
                f"translator_options must be JSON serializable: {exc}",
            ) from exc
        schema = descriptor.options_schema
        unknown = sorted(set(options.translator_options) - set(schema))
        if unknown:
            raise TranslationRegistryError(
                "unknown_option",
                f"Unknown options for engine {descriptor.id}: {', '.join(unknown)}",
            )
        for key, expected in schema.items():
            if key not in options.translator_options:
                continue
            value = options.translator_options[key]
            if not isinstance(value, expected):
                raise TranslationRegistryError(
                    "invalid_option_type",
                    f"Option {key!r} for engine {descriptor.id} must be "
                    f"{_type_name(expected)}, got {type(value).__name__}",
                )

    def create(
        self,
        engine_id: str,
        dependencies: Any,
        options: TranslationOptions,
    ) -> TranslationEngine:
        """Validate a selection and construct one injected engine instance."""
        descriptor = self.get(engine_id)
        if not descriptor.available:
            reason = descriptor.reason or "no availability reason supplied"
            raise TranslationRegistryError(
                "engine_unavailable",
                f"Translation engine {descriptor.id} is unavailable: {reason}",
            )
        self.validate_options(descriptor, options)
        if descriptor.factory is None:
            raise TranslationRegistryError(
                "factory_missing",
                f"Translation engine {descriptor.id} has no factory",
            )
        return descriptor.factory(dependencies, options)


def _type_name(expected: type | tuple[type, ...]) -> str:
    """Format a type or type tuple for a useful validation error."""
    if isinstance(expected, tuple):
        return " or ".join(item.__name__ for item in expected)
    return expected.__name__
