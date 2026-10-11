"""Small, revisioned JSON glossary for standard translation engines."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import time
import unicodedata
from typing import Any, Callable, Iterator, Mapping, Protocol, Sequence


GLOSSARY_SCHEMA = 1
GLOSSARY_REVISION = "translation-glossary-v1"
AtomicWriter = Callable[[Path, str], None]


class GlossaryError(RuntimeError):
    """Typed storage, schema, CAS or proposal error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class GlossaryEntry:
    """One accepted translation keyed by languages, sense and scope."""

    key: str
    source_term: str
    target_term: str
    source_language: str
    target_language: str
    sense: str = ""
    scope: str = ""
    origin: str = "manual"
    revision: int = 0
    evidence: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "source_term": self.source_term,
            "target_term": self.target_term,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "sense": self.sense,
            "scope": self.scope,
            "origin": self.origin,
            "revision": self.revision,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class GlossaryProposal:
    """A proposed term; conflicts never overwrite an accepted entry."""

    proposal_id: str
    key: str
    source_term: str
    target_term: str
    source_language: str
    target_language: str
    sense: str = ""
    scope: str = ""
    origin: str = "model"
    status: str = "proposed"
    revision: int = 0
    evidence: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "key": self.key,
            "source_term": self.source_term,
            "target_term": self.target_term,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "sense": self.sense,
            "scope": self.scope,
            "origin": self.origin,
            "status": self.status,
            "revision": self.revision,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class GlossarySnapshot:
    """Validated immutable view used by a translation run."""

    revision: int = 0
    entries: tuple[GlossaryEntry, ...] = ()
    proposals: tuple[GlossaryProposal, ...] = ()
    history: tuple[Mapping[str, Any], ...] = ()
    schema: int = GLOSSARY_SCHEMA
    format_revision: str = GLOSSARY_REVISION

    def __post_init__(self) -> None:
        if self.schema != GLOSSARY_SCHEMA:
            raise ValueError(f"unsupported glossary schema: {self.schema}")
        if self.revision < 0:
            raise ValueError("glossary revision must not be negative")
        if len({item.key for item in self.entries}) != len(self.entries):
            raise ValueError("glossary entry keys must be unique")
        if len({item.proposal_id for item in self.proposals}) != len(self.proposals):
            raise ValueError("glossary proposal IDs must be unique")
        object.__setattr__(self, "entries", tuple(self.entries))
        object.__setattr__(self, "proposals", tuple(self.proposals))
        object.__setattr__(self, "history", tuple(dict(item) for item in self.history))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "format_revision": self.format_revision,
            "revision": self.revision,
            "entries": [item.to_mapping() for item in self.entries],
            "proposals": [item.to_mapping() for item in self.proposals],
            "history": [dict(item) for item in self.history],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "GlossarySnapshot":
        if not isinstance(value, Mapping) or value.get("schema") != GLOSSARY_SCHEMA:
            raise GlossaryError("invalid_schema", "Unsupported glossary schema")
        try:
            entries = tuple(
                GlossaryEntry(**{**item, "evidence": tuple(item.get("evidence", ()))})
                for item in value.get("entries", ())
            )
            proposals = tuple(
                GlossaryProposal(**{**item, "evidence": tuple(item.get("evidence", ()))})
                for item in value.get("proposals", ())
            )
            snapshot = cls(
                revision=int(value.get("revision", 0)),
                entries=entries,
                proposals=proposals,
                history=tuple(value.get("history", ())),
                schema=int(value["schema"]),
                format_revision=value.get("format_revision", GLOSSARY_REVISION),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GlossaryError("invalid_schema", f"Invalid glossary data: {exc}") from exc
        for proposal in snapshot.proposals:
            if proposal.status not in {"proposed", "conflict", "accepted", "rejected"}:
                raise GlossaryError("invalid_schema", "Invalid glossary proposal status")
        return snapshot


class GlossaryStore(Protocol):
    def load(self) -> GlossarySnapshot:
        ...

    def lookup(
        self, source_term: str, source_language: str, target_language: str,
        *, sense: str = "", scope: str = "",
    ) -> GlossaryEntry | None:
        ...


def _normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split()).casefold()


def glossary_key(source_term: str, source_language: str, target_language: str,
                 *, sense: str = "", scope: str = "") -> str:
    values = (source_language, target_language, source_term, sense, scope)
    if not all(isinstance(value, str) for value in values):
        raise GlossaryError("invalid_entry", "Glossary key fields must be strings")
    if not _normalise(source_term) or not _normalise(source_language) or not _normalise(target_language):
        raise GlossaryError("invalid_entry", "Glossary languages and source term are required")
    return "|".join(_normalise(value) for value in values)


def _normalise_evidence(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray)):
        raise GlossaryError("invalid_entry", "Glossary evidence must be a sequence of IDs")
    try:
        evidence = tuple(value)
    except TypeError as exc:
        raise GlossaryError("invalid_entry", "Glossary evidence must be a sequence of IDs") from exc
    if any(not isinstance(item, str) or not item.strip() for item in evidence):
        raise GlossaryError("invalid_entry", "Glossary evidence IDs must be non-empty strings")
    if len(set(evidence)) != len(evidence):
        raise GlossaryError("invalid_entry", "Glossary evidence IDs must be unique")
    return tuple(item.strip() for item in evidence)



def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _file_lock(path: Path, timeout: float) -> Iterator[None]:
    """Cross-process single-writer lock without importing queue orchestration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise GlossaryError("lock_timeout", f"Glossary lock is busy: {path}")
            time.sleep(0.02)
    try:
        yield
    finally:
        os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class JsonGlossaryStore:
    """JSON glossary with optimistic revision checks and atomic writes."""

    def __init__(self, path: Path, *, atomic_writer: AtomicWriter = _atomic_write,
                 lock_timeout: float = 2.0) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_name(self.path.name + ".lock")
        self.atomic_writer = atomic_writer
        self.lock_timeout = lock_timeout

    def load(self) -> GlossarySnapshot:
        if not self.path.is_file():
            return GlossarySnapshot()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return GlossarySnapshot.from_mapping(value)
        except GlossaryError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GlossaryError("storage_error", f"Cannot read glossary {self.path}: {exc}") from exc

    snapshot = load

    def lookup(self, source_term: str, source_language: str, target_language: str,
               *, sense: str = "", scope: str = "") -> GlossaryEntry | None:
        key = glossary_key(source_term, source_language, target_language, sense=sense, scope=scope)
        return next((item for item in self.load().entries if item.key == key), None)

    def propose(self, source_term: str, target_term: str, source_language: str,
                target_language: str, *, sense: str = "", scope: str = "",
                origin: str = "model", evidence: Sequence[str] = (),
                expected_revision: int | None = None) -> GlossaryProposal:
        key = glossary_key(source_term, source_language, target_language, sense=sense, scope=scope)
        target = target_term.strip() if isinstance(target_term, str) else ""
        if not target:
            raise GlossaryError("invalid_entry", "Glossary target term is required")
        evidence = _normalise_evidence(evidence)
        with _file_lock(self.lock_path, self.lock_timeout):
            current = self.load()
            self._check_revision(current, expected_revision)
            accepted = next((item for item in current.entries if item.key == key), None)
            same = lambda item: item.key == key and _normalise(item.target_term) == _normalise(target)
            if accepted and _normalise(accepted.target_term) == _normalise(target):
                return GlossaryProposal(
                    "accepted:" + key, key, source_term, target, source_language,
                    target_language, sense, scope, origin, "accepted", current.revision,
                    accepted.evidence,
                )
            existing = next((item for item in current.proposals if same(item)), None)
            if existing is not None:
                return existing
            status = "conflict" if accepted else "proposed"
            proposal = GlossaryProposal(
                proposal_id=self._proposal_id(key, target), key=key, source_term=source_term,
                target_term=target, source_language=source_language, target_language=target_language,
                sense=sense, scope=scope, origin=origin, status=status,
                revision=current.revision + 1,
                evidence=evidence,
            )
            history = self._event_history(current, "proposal", proposal)
            updated = GlossarySnapshot(current.revision + 1, current.entries, current.proposals + (proposal,), history)
            self._save(updated)
            return proposal

    def accept(self, proposal_id: str, *, expected_revision: int | None = None) -> GlossaryEntry:
        with _file_lock(self.lock_path, self.lock_timeout):
            current = self.load()
            self._check_revision(current, expected_revision)
            proposal = next((item for item in current.proposals if item.proposal_id == proposal_id), None)
            if proposal is None:
                raise GlossaryError("unknown_proposal", f"Unknown glossary proposal: {proposal_id}")
            if proposal.status == "rejected":
                raise GlossaryError("conflict", "Rejected glossary proposal cannot be accepted")
            if proposal.status == "accepted":
                return GlossaryEntry(
                    proposal.key, proposal.source_term, proposal.target_term,
                    proposal.source_language, proposal.target_language, proposal.sense,
                    proposal.scope, proposal.origin, current.revision, proposal.evidence,
                )
            existing = next((item for item in current.entries if item.key == proposal.key), None)
            if existing and _normalise(existing.target_term) != _normalise(proposal.target_term):
                raise GlossaryError("conflict", "Accepted glossary entry would be overwritten")
            entry = existing or GlossaryEntry(
                proposal.key, proposal.source_term, proposal.target_term,
                proposal.source_language, proposal.target_language, proposal.sense,
                proposal.scope, proposal.origin, current.revision + 1, proposal.evidence,
            )
            proposals = tuple(GlossaryProposal(**{**item.to_mapping(), "status": "accepted"}) if item.proposal_id == proposal_id else item for item in current.proposals)
            entries = current.entries if existing else current.entries + (entry,)
            history = self._event_history(current, "accepted", entry)
            updated = GlossarySnapshot(current.revision + 1, entries, proposals, history)
            self._save(updated)
            return entry

    def reject(self, proposal_id: str, *, expected_revision: int | None = None) -> GlossaryProposal:
        """Reject a proposal explicitly without changing accepted entries."""
        with _file_lock(self.lock_path, self.lock_timeout):
            current = self.load()
            self._check_revision(current, expected_revision)
            proposal = next((item for item in current.proposals if item.proposal_id == proposal_id), None)
            if proposal is None:
                raise GlossaryError("unknown_proposal", f"Unknown glossary proposal: {proposal_id}")
            if proposal.status == "accepted":
                raise GlossaryError("conflict", "Accepted glossary proposal cannot be rejected")
            if proposal.status == "rejected":
                return proposal
            updated_proposal = GlossaryProposal(
                proposal.proposal_id, proposal.key, proposal.source_term, proposal.target_term,
                proposal.source_language, proposal.target_language, proposal.sense,
                proposal.scope, proposal.origin, "rejected", current.revision + 1,
                proposal.evidence,
            )
            proposals = tuple(
                updated_proposal if item.proposal_id == proposal_id else item
                for item in current.proposals
            )
            history = self._event_history(current, "rejected", updated_proposal)
            updated = GlossarySnapshot(current.revision + 1, current.entries, proposals, history)
            self._save(updated)
            return updated_proposal

    def _save(self, snapshot: GlossarySnapshot) -> None:
        try:
            payload = json.dumps(snapshot.to_mapping(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            self.atomic_writer(self.path, payload)
        except (OSError, TypeError, ValueError) as exc:
            raise GlossaryError("storage_error", f"Cannot save glossary {self.path}: {exc}") from exc

    @staticmethod
    def _check_revision(snapshot: GlossarySnapshot, expected: int | None) -> None:
        if expected is not None and expected != snapshot.revision:
            raise GlossaryError("revision_conflict", f"Expected glossary revision {expected}, got {snapshot.revision}")

    @staticmethod
    def _proposal_id(key: str, target: str) -> str:
        digest = hashlib.sha256((key + "\0" + _normalise(target)).encode("utf-8")).hexdigest()[:16]
        return "proposal:" + digest

    @staticmethod
    def _event_history(snapshot: GlossarySnapshot, kind: str, value: Any) -> tuple[Mapping[str, Any], ...]:
        mapping = value.to_mapping() if hasattr(value, "to_mapping") else {"key": value.key}
        return snapshot.history + ({"kind": kind, "revision": snapshot.revision + 1, "value": mapping},)
