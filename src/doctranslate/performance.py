"""Dependency-free performance measurements and report generation."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Any, Iterator


def _safe_field(value: Any) -> str | int | float | bool | None:
    """Keep benchmark metadata small and free of arbitrary payloads."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:128]
    return type(value).__name__


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


@dataclass(frozen=True)
class TimingSample:
    name: str
    elapsed_ms: float
    cpu_ms: float
    fields: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass
class PerformanceRecorder:
    """Collect phase timings without imposing a benchmark framework dependency."""

    metadata: dict[str, Any] = field(default_factory=dict)
    samples: list[TimingSample] = field(default_factory=list)
    counters: dict[str, int | float] = field(default_factory=dict)

    @contextmanager
    def measure(self, name: str, **fields: Any) -> Iterator[None]:
        if not name or not name.strip():
            raise ValueError("Performance sample name must not be empty")
        started = time.perf_counter()
        cpu_started = time.process_time()
        try:
            yield
        finally:
            self.samples.append(TimingSample(
                name=name,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                cpu_ms=(time.process_time() - cpu_started) * 1000,
                fields={key: _safe_field(value) for key, value in fields.items()},
            ))

    def add_sample(self, name: str, elapsed_ms: float, cpu_ms: float = 0.0, **fields: Any) -> None:
        if elapsed_ms < 0 or cpu_ms < 0:
            raise ValueError("Performance durations cannot be negative")
        self.samples.append(TimingSample(
            name=name,
            elapsed_ms=float(elapsed_ms),
            cpu_ms=float(cpu_ms),
            fields={key: _safe_field(value) for key, value in fields.items()},
        ))

    def count(self, name: str, value: int | float = 1) -> None:
        if value < 0:
            raise ValueError("Performance counters cannot be negative")
        self.counters[name] = self.counters.get(name, 0) + value

    def summary(self) -> list[dict[str, Any]]:
        grouped: dict[str, list[TimingSample]] = {}
        for sample in self.samples:
            grouped.setdefault(sample.name, []).append(sample)
        result = []
        for name, samples in grouped.items():
            elapsed = [sample.elapsed_ms for sample in samples]
            cpu = [sample.cpu_ms for sample in samples]
            result.append({
                "name": name,
                "count": len(samples),
                "total_ms": round(sum(elapsed), 3),
                "mean_ms": round(statistics.fmean(elapsed), 3),
                "p50_ms": round(_percentile(elapsed, 0.50), 3),
                "p95_ms": round(_percentile(elapsed, 0.95), 3),
                "min_ms": round(min(elapsed), 3),
                "max_ms": round(max(elapsed), 3),
                "cpu_total_ms": round(sum(cpu), 3),
            })
        return sorted(result, key=lambda item: (-item["total_ms"], item["name"]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": 1,
            "metadata": {key: _safe_field(value) for key, value in self.metadata.items()},
            "counters": self.counters,
            "summary": self.summary(),
            "samples": [{
                "name": sample.name,
                "elapsed_ms": round(sample.elapsed_ms, 3),
                "cpu_ms": round(sample.cpu_ms, 3),
                "fields": sample.fields,
            } for sample in self.samples],
        }

    def write_json(self, path: Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
        return target

    def markdown(self, title: str = "Performance report") -> str:
        lines = [f"# {title}", "", "## Metadata", ""]
        if self.metadata:
            lines.extend(f"- {key}: {value}" for key, value in self.metadata.items())
        else:
            lines.append("- none")
        lines.extend(["", "## Counters", ""])
        if self.counters:
            lines.extend(f"- {key}: {value}" for key, value in self.counters.items())
        else:
            lines.append("- none")
        lines.extend([
            "",
            "## Timing summary",
            "",
            "| Block | Count | Total ms | Mean ms | p50 ms | p95 ms | CPU ms |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for item in self.summary():
            lines.append(
                "| {name} | {count} | {total_ms} | {mean_ms} | {p50_ms} | {p95_ms} | {cpu_total_ms} |".format(
                    **item
                )
            )
        lines.extend(["", "Raw samples are stored in the adjacent JSON report.", ""])
        return "\n".join(lines)

    def write_markdown(self, path: Path, title: str = "Performance report") -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(self.markdown(title), encoding="utf-8")
        os.replace(temporary, target)
        return target
