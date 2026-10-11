"""Managed, bounded memory tools for advanced translation engines.

The model-facing surface is an explicit allowlist. It can query prepared memory
and submit validated proposals, but it never receives a filesystem or raw store
handle.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping, Sequence

from .memory import GlossaryEntry, GlossaryError, GlossaryProposal, GlossarySnapshot, GlossaryStore
from .retrieval import (
    GlossaryCandidate,
    GlossaryIndex,
    OccurrenceCandidate,
    SourceOccurrence,
    search_occurrences,
)


MAX_RESULTS = 64
MAX_TERMS = 32
MAX_SEGMENT_IDS = 64
MAX_QUERY_CHARS = 4096
MAX_SCOPE_CHARS = 256
MAX_REASON_CHARS = 2000
DEFAULT_TOKEN_LIMIT = 2048


class MemoryToolError(ValueError):
    """Typed validation or managed-memory tool error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class MemoryLookupResult:
    matches: tuple[GlossaryCandidate, ...]
    revision: int
    more: bool
    token_count: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "matches": [
                {"entry": item.entry.to_mapping(), "score": item.score}
                for item in self.matches
            ],
            "revision": self.revision,
            "more": self.more,
            "token_count": self.token_count,
        }


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    kind: str
    text: str
    revision: int
    payload: Mapping[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "text": self.text,
            "revision": self.revision,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class MemorySearchResult:
    records: tuple[MemoryRecord, ...]
    revision: int
    more: bool
    token_count: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "records": [item.to_mapping() for item in self.records],
            "revision": self.revision,
            "more": self.more,
            "token_count": self.token_count,
        }


@dataclass(frozen=True)
class OccurrenceResult:
    matches: tuple[OccurrenceCandidate, ...]
    revision: int
    more: bool
    token_count: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "matches": [
                {"occurrence": item.occurrence.__dict__, "score": item.score}
                for item in self.matches
            ],
            "revision": self.revision,
            "more": self.more,
            "token_count": self.token_count,
        }


@dataclass(frozen=True)
class SourceResult:
    segments: tuple[SourceOccurrence, ...]
    revision: int
    more: bool
    token_count: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "segments": [item.__dict__ for item in self.segments],
            "revision": self.revision,
            "more": self.more,
            "token_count": self.token_count,
        }


@dataclass(frozen=True)
class ProposalResult:
    proposal: GlossaryProposal
    evidence: tuple[str, ...]
    revision: int
    dirty_segment_ids: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "proposal": self.proposal.to_mapping(),
            "evidence": list(self.evidence),
            "revision": self.revision,
            "dirty_segment_ids": list(self.dirty_segment_ids),
        }


@dataclass(frozen=True)
class DecisionResult:
    status: str
    proposal: GlossaryProposal
    entry: GlossaryEntry | None
    revision: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "proposal": self.proposal.to_mapping(),
            "entry": self.entry.to_mapping() if self.entry else None,
            "revision": self.revision,
        }


@dataclass(frozen=True)
class RevisionRequest:
    segment_ids: tuple[str, ...]
    reason: str
    revision: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "segment_ids": list(self.segment_ids),
            "reason": self.reason,
            "revision": self.revision,
        }


def _text(value: Any, field: str, *, max_chars: int) -> str:
    if not isinstance(value, str):
        raise MemoryToolError("invalid_schema", f"{field} must be a string")
    result = value.strip()
    if not result:
        raise MemoryToolError("invalid_schema", f"{field} must not be empty")
    if len(result) > max_chars:
        raise MemoryToolError("limit_exceeded", f"{field} is too long")
    return result


def _limit(value: Any, field: str, maximum: int = MAX_RESULTS) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise MemoryToolError(
            "limit_exceeded",
            f"{field} must be an integer between 1 and {maximum}",
        )
    return value


def _token_limit(value: Any) -> int:
    return _limit(value, "token_limit", 16384)


def _terms(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = tuple(value)
    else:
        raise MemoryToolError("invalid_schema", "terms must be a string or a sequence")
    if not values or len(values) > MAX_TERMS:
        raise MemoryToolError("limit_exceeded", f"terms must contain 1..{MAX_TERMS} items")
    return tuple(_text(item, "term", max_chars=MAX_QUERY_CHARS) for item in values)


def _ids(value: Any, field: str = "segment_ids") -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = tuple(value)
    else:
        raise MemoryToolError("invalid_schema", f"{field} must be a string or a sequence")
    if not values or len(values) > MAX_SEGMENT_IDS:
        raise MemoryToolError(
            "limit_exceeded",
            f"{field} must contain 1..{MAX_SEGMENT_IDS} items",
        )
    result = tuple(_text(item, field, max_chars=256) for item in values)
    if len(set(result)) != len(result):
        raise MemoryToolError("invalid_schema", f"{field} must not contain duplicates")
    return result


def _estimate_tokens(value: Any) -> int:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return max(1, (len(encoded) + 3) // 4)


def _context_values(context: Mapping[str, Any] | None) -> dict[str, Any]:
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise MemoryToolError("invalid_schema", "context must be an object")
    allowed = {"source_language", "target_language", "scope", "sense", "document_id"}
    unknown = set(context) - allowed
    if unknown:
        raise MemoryToolError("invalid_schema", f"unknown context fields: {sorted(unknown)}")
    return dict(context)


class MemoryTools:
    """Allowlisted memory facade; the injected store stays private and bounded."""

    TOOL_NAMES = frozenset(
        {
            "lookup_terms",
            "search_memory",
            "get_occurrences",
            "get_source",
            "propose_term",
            "accept_proposal",
            "reject_proposal",
            "request_revision",
        }
    )

    def __init__(
        self,
        store: GlossaryStore,
        *,
        occurrences: Iterable[SourceOccurrence] = (),
        source_segments: Mapping[str, SourceOccurrence | Mapping[str, Any] | str] | None = None,
    ) -> None:
        self._store = store
        self._occurrences = tuple(occurrences)
        self._source_segments = dict(source_segments or {})
        self._dirty_segment_ids: set[str] = set()

    @property
    def dirty_segment_ids(self) -> tuple[str, ...]:
        """Runtime dirty view; persistence remains owned by the checkpoint/store."""
        return tuple(sorted(self._dirty_segment_ids))

    def dispatch(self, name: str, arguments: Mapping[str, Any] | None = None, **kwargs: Any) -> Any:
        """Dispatch only named memory operations; no arbitrary method execution."""
        if not isinstance(name, str) or name not in self.TOOL_NAMES:
            raise MemoryToolError("unknown_tool", f"Unknown memory tool: {name!r}")
        if arguments is not None and kwargs:
            raise MemoryToolError("invalid_schema", "Use arguments or keyword fields, not both")
        payload = dict(arguments or kwargs)
        return getattr(self, name)(**payload)

    def lookup_terms(
        self,
        terms: str | Sequence[str],
        context: Mapping[str, Any] | None = None,
        *,
        source_language: str | None = None,
        target_language: str | None = None,
        scope: str = "",
        sense: str = "",
        limit: int = 8,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ) -> MemoryLookupResult:
        values = _context_values(context)
        source_language = source_language or values.get("source_language")
        target_language = target_language or values.get("target_language")
        source_language = _text(source_language, "source_language", max_chars=64)
        target_language = _text(target_language, "target_language", max_chars=64)
        scope = _text(scope or values.get("scope", "default"), "scope", max_chars=MAX_SCOPE_CHARS)
        sense = _text(sense or values.get("sense", ""), "sense", max_chars=MAX_SCOPE_CHARS) if sense or values.get("sense") else ""
        values_terms = _terms(terms)
        limit = _limit(limit, "limit")
        token_limit = _token_limit(token_limit)

        snapshot = self._store.load()
        index = GlossaryIndex(snapshot)
        found: dict[str, GlossaryCandidate] = {}
        more = False
        for term in values_terms:
            candidates, candidates_more = index.search(
                term,
                source_language,
                target_language,
                scope=scope if scope != "default" else "",
                sense=sense,
                limit=MAX_RESULTS,
            )
            more = more or candidates_more
            for candidate in candidates:
                current = found.get(candidate.entry.key)
                if current is None or candidate.score > current.score:
                    found[candidate.entry.key] = candidate
        ordered = sorted(found.values(), key=lambda item: (-item.score, item.entry.key))
        selected: list[GlossaryCandidate] = []
        used = 0
        for candidate in ordered:
            cost = _estimate_tokens({"entry": candidate.entry.to_mapping(), "score": candidate.score})
            if len(selected) >= limit or used + cost > token_limit:
                more = True
                continue
            selected.append(candidate)
            used += cost
        return MemoryLookupResult(tuple(selected), snapshot.revision, more, used)

    def search_memory(
        self,
        query: str,
        scope: str = "",
        *,
        limit: int = 8,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ) -> MemorySearchResult:
        query = _text(query, "query", max_chars=MAX_QUERY_CHARS)
        scope = _text(scope, "scope", max_chars=MAX_SCOPE_CHARS) if scope else ""
        limit = _limit(limit, "limit")
        token_limit = _token_limit(token_limit)
        snapshot = self._store.load()
        query_fold = query.casefold()
        records: list[MemoryRecord] = []
        for index, event in enumerate(snapshot.history):
            payload = dict(event.get("value", {})) if isinstance(event, Mapping) else {}
            event_scope = str(payload.get("scope", ""))
            text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
            if scope and event_scope.casefold() != scope.casefold():
                continue
            if query_fold not in text.casefold():
                continue
            record_id = str(payload.get("proposal_id") or payload.get("key") or f"history:{index}")
            records.append(
                MemoryRecord(
                    record_id=record_id,
                    kind=str(event.get("kind", "memory")),
                    text=text,
                    revision=int(event.get("revision", 0)),
                    payload=payload,
                )
            )
        records.sort(key=lambda item: (item.revision, item.record_id), reverse=True)
        selected: list[MemoryRecord] = []
        used = 0
        more = len(records) > limit
        for record in records:
            cost = _estimate_tokens(record.to_mapping())
            if len(selected) >= limit or used + cost > token_limit:
                more = True
                continue
            selected.append(record)
            used += cost
        return MemorySearchResult(tuple(selected), snapshot.revision, more, used)

    def get_occurrences(
        self,
        term: str,
        *,
        limit: int = 4,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ) -> OccurrenceResult:
        term = _text(term, "term", max_chars=MAX_QUERY_CHARS)
        limit = _limit(limit, "limit")
        token_limit = _token_limit(token_limit)
        snapshot = self._store.load()
        found, more = search_occurrences(term, self._occurrences, limit=MAX_RESULTS)
        selected: list[OccurrenceCandidate] = []
        used = 0
        for item in found:
            cost = _estimate_tokens({"occurrence": item.occurrence.__dict__, "score": item.score})
            if len(selected) >= limit or used + cost > token_limit:
                more = True
                continue
            selected.append(item)
            used += cost
        return OccurrenceResult(tuple(selected), snapshot.revision, more, used)

    def get_source(
        self,
        segment_ids: str | Sequence[str],
        *,
        limit: int = MAX_SEGMENT_IDS,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ) -> SourceResult:
        ids = _ids(segment_ids)
        limit = _limit(limit, MAX_SEGMENT_IDS)
        token_limit = _token_limit(token_limit)
        available = dict(self._source_segments)
        available.update({item.segment_id: item for item in self._occurrences})
        missing = [segment_id for segment_id in ids if segment_id not in available]
        if missing:
            raise MemoryToolError("unknown_segment", f"Unknown segment IDs: {missing}")
        snapshot = self._store.load()
        selected: list[SourceOccurrence] = []
        used = 0
        more = len(ids) > limit
        for segment_id in ids[:limit]:
            item = available[segment_id]
            if isinstance(item, SourceOccurrence):
                occurrence = item
            elif isinstance(item, str):
                occurrence = SourceOccurrence(segment_id, item, "")
            elif isinstance(item, Mapping):
                try:
                    occurrence = SourceOccurrence(
                        segment_id=str(item.get("segment_id", segment_id)),
                        source_text=_text(item.get("source_text"), "source_text", max_chars=MAX_QUERY_CHARS),
                        translated_text=str(item.get("translated_text", "")),
                        page_number=item.get("page_number"),
                    )
                except (TypeError, ValueError) as exc:
                    raise MemoryToolError("invalid_schema", f"Invalid source segment: {exc}") from exc
            else:
                raise MemoryToolError("invalid_schema", f"Unsupported source segment: {segment_id}")
            cost = _estimate_tokens(occurrence.__dict__)
            if used + cost > token_limit:
                more = True
                continue
            selected.append(occurrence)
            used += cost
        return SourceResult(tuple(selected), snapshot.revision, more, used)

    def propose_term(
        self,
        entry: Mapping[str, Any],
        evidence: Sequence[str] = (),
        *,
        expected_revision: int | None = None,
    ) -> ProposalResult:
        if not isinstance(entry, Mapping):
            raise MemoryToolError("invalid_schema", "entry must be an object")
        required = ("source_term", "target_term", "source_language", "target_language")
        unknown = set(entry) - set(required) - {"sense", "scope", "origin"}
        if unknown:
            raise MemoryToolError("invalid_schema", f"unknown entry fields: {sorted(unknown)}")
        values = {key: entry.get(key, "") for key in required + ("sense", "scope", "origin")}
        values["source_term"] = _text(values["source_term"], "source_term", max_chars=MAX_QUERY_CHARS)
        values["target_term"] = _text(values["target_term"], "target_term", max_chars=MAX_QUERY_CHARS)
        values["source_language"] = _text(values["source_language"], "source_language", max_chars=64)
        values["target_language"] = _text(values["target_language"], "target_language", max_chars=64)
        values["sense"] = _text(values["sense"], "sense", max_chars=MAX_SCOPE_CHARS) if values["sense"] else ""
        values["scope"] = _text(values["scope"], "scope", max_chars=MAX_SCOPE_CHARS) if values["scope"] else ""
        values["origin"] = _text(values["origin"], "origin", max_chars=64) if values["origin"] else "model"
        if expected_revision is None or isinstance(expected_revision, bool) or expected_revision < 0:
            raise MemoryToolError("missing_revision", "propose_term requires expected_revision")
        evidence_ids = _ids(evidence, "evidence") if evidence else ()
        try:
            proposal = self._store.propose(**values, evidence=evidence_ids, expected_revision=expected_revision)
        except GlossaryError as exc:
            raise MemoryToolError(exc.code, str(exc)) from exc
        except TypeError as exc:
            raise MemoryToolError("store_capability", "Glossary store does not support evidence proposals") from exc
        self._dirty_segment_ids.update(evidence_ids)
        snapshot = self._store.load()
        return ProposalResult(proposal, evidence_ids, snapshot.revision, self.dirty_segment_ids)

    def accept_proposal(
        self,
        proposal_id: str,
        *,
        expected_revision: int | None = None,
    ) -> DecisionResult:
        proposal_id = _text(proposal_id, "proposal_id", max_chars=256)
        expected_revision = self._required_revision(expected_revision)
        try:
            entry = self._store.accept(proposal_id, expected_revision=expected_revision)
        except GlossaryError as exc:
            raise MemoryToolError(exc.code, str(exc)) from exc
        except AttributeError as exc:
            raise MemoryToolError("store_capability", "Glossary store does not support accept") from exc
        snapshot = self._store.load()
        proposal = self._proposal(snapshot, proposal_id)
        self._dirty_segment_ids.update(proposal.evidence)
        return DecisionResult("accepted", proposal, entry, snapshot.revision)

    def reject_proposal(
        self,
        proposal_id: str,
        *,
        expected_revision: int | None = None,
    ) -> DecisionResult:
        proposal_id = _text(proposal_id, "proposal_id", max_chars=256)
        expected_revision = self._required_revision(expected_revision)
        try:
            proposal = self._store.reject(proposal_id, expected_revision=expected_revision)
        except GlossaryError as exc:
            raise MemoryToolError(exc.code, str(exc)) from exc
        except AttributeError as exc:
            raise MemoryToolError("store_capability", "Glossary store does not support reject") from exc
        snapshot = self._store.load()
        current = self._proposal(snapshot, proposal_id)
        self._dirty_segment_ids.update(current.evidence)
        return DecisionResult("rejected", current, None, snapshot.revision)

    def request_revision(
        self,
        segment_ids: str | Sequence[str],
        reason: str,
        *,
        expected_revision: int | None = None,
    ) -> RevisionRequest:
        ids = _ids(segment_ids)
        reason = _text(reason, "reason", max_chars=MAX_REASON_CHARS)
        if expected_revision is not None and (
            isinstance(expected_revision, bool) or expected_revision < 0
        ):
            raise MemoryToolError("invalid_schema", "expected_revision must be a non-negative integer")
        revision = self._store.load().revision
        if expected_revision is not None and expected_revision != revision:
            raise MemoryToolError(
                "revision_conflict",
                f"Expected glossary revision {expected_revision}, got {revision}",
            )
        self._dirty_segment_ids.update(ids)
        return RevisionRequest(ids, reason, revision)

    @staticmethod
    def _required_revision(value: int | None) -> int:
        if value is None or isinstance(value, bool) or value < 0:
            raise MemoryToolError("missing_revision", "mutation requires expected_revision")
        return value

    @staticmethod
    def _proposal(snapshot: GlossarySnapshot, proposal_id: str) -> GlossaryProposal:
        proposal = next((item for item in snapshot.proposals if item.proposal_id == proposal_id), None)
        if proposal is None:
            raise MemoryToolError("unknown_proposal", f"Unknown proposal: {proposal_id}")
        return proposal
