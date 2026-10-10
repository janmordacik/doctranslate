"""Format discovery and selection without importing optional adapters eagerly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal


Direction = Literal["input", "output"]


@dataclass(frozen=True)
class Availability:
    available: bool
    code: str = "available"
    reason: str = ""
    remedy: str = ""


@dataclass(frozen=True)
class FormatDescriptor:
    id: str
    label: str
    media_type: str
    extensions: tuple[str, ...]
    factory: Callable[[], Any]
    direction: Direction
    check_availability: Callable[[], Availability] | None = None

    def availability(self) -> Availability:
        if self.check_availability is None:
            return Availability(True)
        return self.check_availability()


class FormatSelectionError(LookupError):
    """A format cannot be selected unambiguously or is unavailable."""

    def __init__(self, message: str, *, code: str = "format_error") -> None:
        super().__init__(message)
        self.code = code


class FormatRegistry:
    """Two directional registries with deterministic extension resolution."""

    def __init__(self) -> None:
        self._items: dict[Direction, dict[str, FormatDescriptor]] = {
            "input": {},
            "output": {},
        }

    def register(self, descriptor: FormatDescriptor) -> None:
        if descriptor.id in self._items[descriptor.direction]:
            raise FormatSelectionError(
                f"Duplicate {descriptor.direction} format: {descriptor.id}",
                code="duplicate_format",
            )
        if not descriptor.extensions:
            raise ValueError("A format needs at least one extension")
        self._items[descriptor.direction][descriptor.id] = descriptor

    def descriptors(self, direction: Direction) -> tuple[FormatDescriptor, ...]:
        return tuple(sorted(self._items[direction].values(), key=lambda item: item.id))

    def get(self, direction: Direction, format_id: str) -> FormatDescriptor:
        try:
            return self._items[direction][format_id.lower()]
        except KeyError as exc:
            available = ", ".join(item.id for item in self.descriptors(direction)) or "(none)"
            raise FormatSelectionError(
                f"Unknown {direction} format {format_id!r}; available: {available}",
                code="unknown_format",
            ) from exc

    def resolve(
        self,
        direction: Direction,
        path: Path | str,
        explicit_format: str | None = None,
    ) -> FormatDescriptor:
        if explicit_format:
            descriptor = self.get(direction, explicit_format)
            self._ensure_available(descriptor)
            return descriptor
        suffix = Path(path).suffix.lower()
        candidates = [
            item for item in self._items[direction].values()
            if suffix in {extension.lower() for extension in item.extensions}
        ]
        if len(candidates) > 1:
            raise FormatSelectionError(
                f"Extension {suffix or '(none)'} is ambiguous for {direction}: "
                + ", ".join(item.id for item in sorted(candidates, key=lambda item: item.id)),
                code="format_conflict",
            )
        if not candidates:
            raise FormatSelectionError(
                f"Cannot infer {direction} format from {Path(path).name!r}; specify --{direction}-format",
                code="format_required",
            )
        descriptor = candidates[0]
        self._ensure_available(descriptor)
        return descriptor

    def create(
        self,
        direction: Direction,
        path: Path | str,
        explicit_format: str | None = None,
    ) -> Any:
        return self.resolve(direction, path, explicit_format).factory()

    @staticmethod
    def _ensure_available(descriptor: FormatDescriptor) -> None:
        result = descriptor.availability()
        if not result.available:
            remedy = f" Remedy: {result.remedy}" if result.remedy else ""
            raise FormatSelectionError(
                f"Format {descriptor.id} is unavailable: {result.reason}.{remedy}",
                code=result.code,
            )


def _pdf_available() -> Availability:
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        return Availability(
            False,
            code="missing_dependency",
            reason="PyMuPDF is not installed",
            remedy="install the project PDF extra",
        )
    return Availability(True)


def build_default_registry() -> FormatRegistry:
    """Build descriptors only; factories import optional modules on use."""
    registry = FormatRegistry()

    def pdf_input():
        from doctranslate.translate_core.pdf_adapter import PdfInputAdapter
        return PdfInputAdapter()

    def pdf_output():
        from doctranslate.translate_core.pdf_adapter import PdfOutputAdapter
        return PdfOutputAdapter()

    registry.register(FormatDescriptor(
        "pdf", "PDF", "application/pdf", (".pdf",), pdf_input, "input", _pdf_available
    ))
    registry.register(FormatDescriptor(
        "pdf", "PDF", "application/pdf", (".pdf",), pdf_output, "output", _pdf_available
    ))
    return registry
