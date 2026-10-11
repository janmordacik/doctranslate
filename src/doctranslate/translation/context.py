"""Bounded, structured context envelopes for translation requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .memory import GlossarySnapshot
from .planning import ConservativeTokenCounter, TokenCounter
from .retrieval import GlossaryCandidate, GlossaryIndex, SourceOccurrence, search_occurrences


class ContextTooLargeError(ValueError):
    """The source itself cannot fit after mandatory prompt reservations."""


@dataclass(frozen=True)
class ContextBudget:
    max_context_tokens: int
    instruction_tokens: int = 0
    schema_tokens: int = 0
    reserved_output_tokens: int = 0

    @property
    def content_tokens(self) -> int:
        return self.max_context_tokens - self.instruction_tokens - self.schema_tokens - self.reserved_output_tokens

    def __post_init__(self) -> None:
        if self.max_context_tokens <= 0 or self.content_tokens <= 0:
            raise ValueError("context budget leaves no room for source content")
        if any(value < 0 for value in (self.instruction_tokens, self.schema_tokens, self.reserved_output_tokens)):
            raise ValueError("context reservations must not be negative")


@dataclass(frozen=True)
class ContextEnvelope:
    """Structured request data; read-only context never becomes source output."""

    source_text: str
    source_language: str
    target_language: str
    instructions: str
    glossary: tuple[GlossaryCandidate, ...] = ()
    occurrences: tuple[SourceOccurrence, ...] = ()
    glossary_more: bool = False
    occurrences_more: bool = False
    token_method: str = "estimated"
    content_tokens: int = 0

    def to_mapping(self) -> dict[str, Any]:
        return {
            "instructions": self.instructions,
            "source": {
                "language": self.source_language,
                "text": self.source_text,
            },
            "target_language": self.target_language,
            "context": {
                "glossary": [item.entry.to_mapping() for item in self.glossary],
                "occurrences": [item.__dict__ for item in self.occurrences],
                "glossary_more": self.glossary_more,
                "occurrences_more": self.occurrences_more,
            },
        }


class ContextBuilder:
    """Select the smallest deterministic relevant memory view that fits."""

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or ConservativeTokenCounter()

    def build(
        self, source_text: str, source_language: str, target_language: str,
        *, budget: ContextBudget, instructions: str = "", schema_text: str = "",
        memory: GlossarySnapshot | None = None,
        aliases: Mapping[str, Sequence[str]] | None = None,
        occurrences: Sequence[SourceOccurrence] = (),
        sense: str = "", scope: str = "",
        glossary_limit: int = 8, occurrence_limit: int = 4,
    ) -> ContextEnvelope:
        source_tokens = self._count(source_text)
        if source_tokens > budget.content_tokens:
            raise ContextTooLargeError("source segment does not fit the reserved context budget")
        remaining = budget.content_tokens - source_tokens
        index = GlossaryIndex(memory or GlossarySnapshot(), aliases)
        glossary, glossary_more = index.search(
            source_text, source_language, target_language, sense=sense, scope=scope, limit=glossary_limit
        )
        selected_glossary: list[GlossaryCandidate] = []
        for item in glossary:
            if self._count(self._glossary_text(item)) > remaining:
                glossary_more = True
                continue
            selected_glossary.append(item)
            remaining -= self._count(self._glossary_text(item))
        found_occurrences, occurrences_more = search_occurrences(source_text, occurrences, occurrence_limit)
        selected_occurrences: list[SourceOccurrence] = []
        for item in found_occurrences:
            text = item.occurrence.source_text + " => " + item.occurrence.translated_text
            if self._count(text) > remaining:
                occurrences_more = True
                continue
            selected_occurrences.append(item.occurrence)
            remaining -= self._count(text)
        used = budget.content_tokens - remaining
        method = "estimated" if isinstance(self.token_counter, ConservativeTokenCounter) else "measured"
        return ContextEnvelope(
            source_text=source_text, source_language=source_language, target_language=target_language,
            instructions=instructions, glossary=tuple(selected_glossary), occurrences=tuple(selected_occurrences),
            glossary_more=glossary_more, occurrences_more=occurrences_more, token_method=method, content_tokens=used,
        )

    @staticmethod
    def _glossary_text(item: GlossaryCandidate) -> str:
        return item.entry.source_term + " => " + item.entry.target_term

    def _count(self, text: str) -> int:
        return int(self.token_counter.count(text))
