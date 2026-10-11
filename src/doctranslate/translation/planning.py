"""Deterministic semantic batching for context-bounded translation engines."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Protocol, Sequence

from ..translate_core.contracts import XhtmlBlock


class SegmentTooLargeError(ValueError):
    """A protected or indivisible text unit cannot fit the input budget."""


@dataclass(frozen=True)
class TokenEstimate:
    """Token count plus its provenance; fallback estimates are never hidden."""

    value: int
    method: str

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("token estimate must not be negative")
        if self.method not in {"measured", "estimated"}:
            raise ValueError("token estimate method must be measured or estimated")


class TokenCounter(Protocol):
    """Minimal injectable tokenizer boundary used by the planner."""

    def count(self, text: str) -> int:
        """Return the number of input tokens for one text value."""


class ConservativeTokenCounter:
    """Portable fallback: reserve one token per three UTF-8-ish characters."""

    def count(self, text: str) -> int:
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 3))


@dataclass(frozen=True)
class PlanningBudget:
    """Context budget split into non-content reservations and input space."""

    max_context_tokens: int
    instruction_tokens: int = 0
    schema_tokens: int = 0
    reserved_output_tokens: int = 0

    def __post_init__(self) -> None:
        values = (
            self.max_context_tokens,
            self.instruction_tokens,
            self.schema_tokens,
            self.reserved_output_tokens,
        )
        if any(value < 0 for value in values):
            raise ValueError("planning budget values must not be negative")
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        if self.input_tokens <= 0:
            raise ValueError("reserved context leaves no input token budget")

    @property
    def input_tokens(self) -> int:
        return self.max_context_tokens - self.instruction_tokens - self.schema_tokens - self.reserved_output_tokens


@dataclass(frozen=True)
class SegmentPart:
    """One lossless source slice; split parts retain the original block ID."""

    part_id: str
    source_block_id: str
    part_index: int
    text: str
    page_number: int
    order: int
    markup: str


@dataclass(frozen=True)
class PlannedSegment:
    """A stable, ordered batch and its exact source-part mapping."""

    segment_id: str
    parts: tuple[SegmentPart, ...]
    input_text: str
    estimated_input_tokens: int
    token_method: str
    page_numbers: tuple[int, ...]
    source_block_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("planned segment must contain at least one part")
        if self.token_method not in {"measured", "estimated"}:
            raise ValueError("token_method must be measured or estimated")


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class SemanticBatchPlanner:
    """Pack paragraph/sentence parts without losing source identity or order."""

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or ConservativeTokenCounter()

    def plan(
        self,
        blocks: Sequence[XhtmlBlock],
        budget: PlanningBudget,
    ) -> tuple[PlannedSegment, ...]:
        """Return deterministic batches; page numbers remain metadata only."""
        parts: list[SegmentPart] = []
        for block in blocks:
            parts.extend(self._parts_for_block(block, budget.input_tokens))
        if not parts:
            return ()

        segments: list[PlannedSegment] = []
        current: list[SegmentPart] = []
        for part in parts:
            candidate = current + [part]
            estimate = self._estimate(self._join_text(candidate))
            if current and estimate.value > budget.input_tokens:
                segments.append(self._make_segment(current))
                current = []
                estimate = self._estimate(part.text)
            if estimate.value > budget.input_tokens:
                raise SegmentTooLargeError(
                    f"Part {part.part_id!r} exceeds input budget {budget.input_tokens} tokens"
                )
            current.append(part)
        if current:
            segments.append(self._make_segment(current))
        return tuple(segments)

    def _parts_for_block(self, block: XhtmlBlock, limit: int) -> list[SegmentPart]:
        text = block.text or ""
        if self._estimate(text).value <= limit:
            return [self._part(block, 0, text)]
        sentences = self._split_sentences(text, block.attributes)
        if len(sentences) == 1:
            raise SegmentTooLargeError(
                f"Block {block.block_id!r} contains an indivisible oversized sentence"
            )
        result: list[SegmentPart] = []
        for index, sentence in enumerate(sentences):
            if self._estimate(sentence).value > limit:
                raise SegmentTooLargeError(
                    f"Sentence {block.block_id!r}:{index} exceeds input budget {limit} tokens"
                )
            result.append(self._part(block, index, sentence))
        return result

    @staticmethod
    def _part(block: XhtmlBlock, index: int, text: str) -> SegmentPart:
        return SegmentPart(
            part_id=f"{block.block_id}:{index}",
            source_block_id=block.block_id,
            part_index=index,
            text=text,
            page_number=block.page_number,
            order=block.order,
            markup=block.markup,
        )

    def _estimate(self, text: str) -> TokenEstimate:
        value = int(self.token_counter.count(text))
        if value < 0:
            raise ValueError("token counter returned a negative value")
        method = "estimated" if isinstance(self.token_counter, ConservativeTokenCounter) else "measured"
        return TokenEstimate(value, method)

    @staticmethod
    def _join_text(parts: Sequence[SegmentPart]) -> str:
        # Separators are batch framing, not source output; each part remains
        # independently addressable for the bridge that reconstructs XHTML.
        return "\n\n".join(part.text for part in parts)

    @staticmethod
    def _split_sentences(text: str, attributes: Any) -> list[str]:
        protected = SemanticBatchPlanner._protected_ranges(text, attributes)
        result: list[str] = []
        start = 0
        for match in _SENTENCE_BOUNDARY.finditer(text):
            cut = match.end()
            if any(begin <= match.start() <= end for begin, end in protected):
                continue
            result.append(text[start:cut])
            start = cut
        result.append(text[start:])
        return [item for item in result if item] or [""]

    @staticmethod
    def _protected_ranges(text: str, attributes: Any) -> tuple[tuple[int, int], ...]:
        if not isinstance(attributes, dict):
            return ()
        ranges: list[tuple[int, int]] = []
        for value in attributes.get("protected_ranges", ()):
            if isinstance(value, (tuple, list)) and len(value) == 2:
                begin, end = value
                if isinstance(begin, int) and isinstance(end, int) and 0 <= begin < end <= len(text):
                    ranges.append((begin, end))
        for fragment in attributes.get("protected_fragments", ()):
            if not isinstance(fragment, str) or not fragment:
                continue
            offset = 0
            while True:
                begin = text.find(fragment, offset)
                if begin < 0:
                    break
                ranges.append((begin, begin + len(fragment)))
                offset = begin + len(fragment)
        return tuple(ranges)

    def _make_segment(self, parts: Sequence[SegmentPart]) -> PlannedSegment:
        frozen = tuple(parts)
        estimate = self._estimate(self._join_text(frozen))
        source_ids = tuple(dict.fromkeys(part.source_block_id for part in frozen))
        return PlannedSegment(
            segment_id=f"{frozen[0].source_block_id}:segment:{frozen[0].part_index}",
            parts=frozen,
            input_text=self._join_text(frozen),
            estimated_input_tokens=estimate.value,
            token_method=estimate.method,
            page_numbers=tuple(dict.fromkeys(part.page_number for part in frozen)),
            source_block_ids=source_ids,
        )


def flatten_parts(segments: Sequence[PlannedSegment]) -> tuple[SegmentPart, ...]:
    """Return parts in source order for loss/duplication validation."""
    return tuple(part for segment in segments for part in segment.parts)
