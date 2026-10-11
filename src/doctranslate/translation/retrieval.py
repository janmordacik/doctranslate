"""Deterministic in-memory retrieval over the approved glossary and occurrences."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping, Sequence

from .memory import GlossaryEntry, GlossarySnapshot


@dataclass(frozen=True)
class GlossaryCandidate:
    entry: GlossaryEntry
    score: int


@dataclass(frozen=True)
class SourceOccurrence:
    segment_id: str
    source_text: str
    translated_text: str
    page_number: int | None = None


@dataclass(frozen=True)
class OccurrenceCandidate:
    occurrence: SourceOccurrence
    score: int


def _fold(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _terms(value: str) -> frozenset[str]:
    return frozenset(re.findall(r"[\wÀ-ž]+", _fold(value), flags=re.UNICODE))


class GlossaryIndex:
    """RAM index; the JSON store remains the source of truth."""

    def __init__(self, snapshot: GlossarySnapshot, aliases: Mapping[str, Sequence[str]] | None = None) -> None:
        self.snapshot = snapshot
        self.aliases = {key: tuple(values) for key, values in (aliases or {}).items()}

    def search(
        self, query: str, source_language: str, target_language: str, *,
        sense: str = "", scope: str = "", limit: int = 8,
    ) -> tuple[tuple[GlossaryCandidate, ...], bool]:
        if limit < 0:
            raise ValueError("limit must not be negative")
        query_fold = _fold(query)
        query_terms = _terms(query)
        candidates: list[GlossaryCandidate] = []
        for entry in self.snapshot.entries:
            if _fold(entry.source_language) != _fold(source_language) or _fold(entry.target_language) != _fold(target_language):
                continue
            if sense and _fold(entry.sense) != _fold(sense):
                continue
            if scope and _fold(entry.scope) != _fold(scope):
                continue
            variants = (entry.source_term,) + self.aliases.get(entry.key, ())
            scores = [self._score(query_fold, query_terms, variant) for variant in variants]
            score = max(scores, default=0)
            if score > 0:
                candidates.append(GlossaryCandidate(entry, score))
        candidates.sort(key=lambda item: (-item.score, item.entry.key))
        return tuple(candidates[:limit]), len(candidates) > limit

    @staticmethod
    def _score(query_fold: str, query_terms: frozenset[str], variant: str) -> int:
        value = _fold(variant)
        if not value:
            return 0
        if value == query_fold:
            return 100
        if re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", query_fold):
            return 90
        variant_terms = _terms(value)
        overlap = len(variant_terms & query_terms)
        if overlap == 0:
            return 0
        return 20 + overlap * 5


def search_occurrences(query: str, occurrences: Iterable[SourceOccurrence], limit: int = 4) -> tuple[tuple[OccurrenceCandidate, ...], bool]:
    """Find bounded lexical evidence with stable segment-ID tie breaking."""
    if limit < 0:
        raise ValueError("limit must not be negative")
    query_fold = _fold(query)
    query_terms = _terms(query)
    found: list[OccurrenceCandidate] = []
    for occurrence in occurrences:
        source = _fold(occurrence.source_text)
        if not source:
            continue
        if source == query_fold:
            score = 100
        elif query_fold and query_fold in source:
            score = 90
        else:
            score = len(_terms(occurrence.source_text) & query_terms) * 5
        if score:
            found.append(OccurrenceCandidate(occurrence, score))
    found.sort(key=lambda item: (-item.score, item.occurrence.segment_id))
    return tuple(found[:limit]), len(found) > limit
