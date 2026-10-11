"""Versioned, self-authored fixtures for translation benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.resources
import json
from typing import Any, Mapping


class BenchmarkFixtureError(ValueError):
    """Raised when a benchmark fixture is incomplete or inconsistent."""


@dataclass(frozen=True)
class BenchmarkFixture:
    """One deterministic translation input and its non-authoritative references."""

    id: str
    version: str
    source_language: str
    target_language: str
    source: str
    references: tuple[str, ...]
    provenance: str
    content_hash: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BenchmarkFixture":
        def text(name: str) -> str:
            item = value.get(name)
            if not isinstance(item, str) or not item.strip():
                raise BenchmarkFixtureError(f"Fixture field {name!r} must be non-empty text")
            return item.strip()

        references = value.get("references")
        if not isinstance(references, list) or not references or any(
            not isinstance(item, str) or not item.strip() for item in references
        ):
            raise BenchmarkFixtureError("Fixture references must be a non-empty string list")
        source = text("source")
        content_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        declared_hash = value.get("content_hash")
        if declared_hash is not None and declared_hash != content_hash:
            raise BenchmarkFixtureError(f"Fixture {value.get('id', '<unknown>')} hash mismatch")
        return cls(
            id=text("id"),
            version=text("version"),
            source_language=text("source_language").lower(),
            target_language=text("target_language").lower(),
            source=source,
            references=tuple(item.strip() for item in references),
            provenance=text("provenance"),
            content_hash=content_hash,
        )


def load_builtin_fixtures() -> tuple[BenchmarkFixture, ...]:
    """Load and validate the immutable built-in benchmark catalogue."""

    raw = (
        importlib.resources.files("doctranslate.ai.data")
        .joinpath("benchmark.json")
        .read_text(encoding="utf-8")
    )
    payload = json.loads(raw)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("fixtures"), list):
        raise BenchmarkFixtureError("Benchmark catalogue must contain a fixtures list")
    fixtures = tuple(BenchmarkFixture.from_dict(item) for item in payload["fixtures"])
    ids = [fixture.id for fixture in fixtures]
    if len(ids) != len(set(ids)):
        raise BenchmarkFixtureError("Benchmark catalogue contains duplicate fixture ids")
    return fixtures
