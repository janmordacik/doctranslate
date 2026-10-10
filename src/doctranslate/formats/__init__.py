"""Document format plugins and their explicit runtime registry."""

from .registry import (
    Availability,
    FormatDescriptor,
    FormatRegistry,
    FormatSelectionError,
    build_default_registry,
)

__all__ = [
    "Availability",
    "FormatDescriptor",
    "FormatRegistry",
    "FormatSelectionError",
    "build_default_registry",
]
