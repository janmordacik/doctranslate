"""Provider-neutral benchmark runner for deterministic translation fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
import threading
import time
from typing import Callable, Iterable

from .benchmark_fixtures import BenchmarkFixture
from .contracts import AiBackend, BackendError


@dataclass(frozen=True)
class BenchmarkSample:
    """One measured translation attempt, including failures and skips."""

    model: str
    fixture_id: str
    fixture_hash: str
    target_variant: str
    run_index: int
    status: str
    text: str = ""
    wall_ms: float | None = None
    load_ms: float | None = None
    prompt_eval_ms: float | None = None
    eval_ms: float | None = None
    prompt_tokens: int | None = None
    eval_tokens: int | None = None
    tokens_per_second: float | None = None
    error_code: str | None = None
    skip_reason: str | None = None


@dataclass(frozen=True)
class BenchmarkResult:
    """Ordered samples and aggregate timing helpers for one benchmark run."""

    samples: tuple[BenchmarkSample, ...]
    interrupted: bool = False

    def successful(self, model: str | None = None) -> tuple[BenchmarkSample, ...]:
        return tuple(
            sample
            for sample in self.samples
            if sample.status == "ok" and (model is None or sample.model == model)
        )

    def warm_median_ms(self, model: str) -> float | None:
        values = [
            sample.wall_ms
            for sample in self.successful(model)
            if sample.run_index > 0 and sample.wall_ms is not None
        ]
        return float(median(values)) if values else None


class BenchmarkRunner:
    """Run equal fixture inputs through independently created provider backends."""

    def __init__(
        self,
        backend_factory: Callable[[str], AiBackend],
        *,
        repeats: int = 4,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if repeats < 1:
            raise ValueError("repeats must be positive")
        self.backend_factory = backend_factory
        self.repeats = repeats
        self.clock = clock

    def run(
        self,
        models: Iterable[str],
        fixture: BenchmarkFixture,
        *,
        target_variant: str = "auto",
        cancel_event: threading.Event | None = None,
    ) -> BenchmarkResult:
        samples: list[BenchmarkSample] = []
        interrupted = False
        for model in models:
            if cancel_event is not None and cancel_event.is_set():
                interrupted = True
                break
            try:
                backend = self.backend_factory(model)
            except BackendError as exc:
                samples.append(
                    BenchmarkSample(
                        model,
                        fixture.id,
                        fixture.content_hash,
                        target_variant,
                        0,
                        "skip",
                        error_code=exc.code,
                        skip_reason=str(exc),
                    )
                )
                continue
            except Exception as exc:
                samples.append(
                    BenchmarkSample(
                        model,
                        fixture.id,
                        fixture.content_hash,
                        target_variant,
                        0,
                        "skip",
                        error_code="backend_unavailable",
                        skip_reason=str(exc),
                    )
                )
                continue

            for run_index in range(self.repeats):
                if cancel_event is not None and cancel_event.is_set():
                    interrupted = True
                    break
                started = self.clock()
                try:
                    text = backend.translate(
                        fixture.source,
                        fixture.source_language,
                        fixture.target_language,
                        target_variant=target_variant,
                    )
                    wall_ms = (self.clock() - started) * 1000
                    samples.append(
                        BenchmarkSample(
                            model,
                            fixture.id,
                            fixture.content_hash,
                            target_variant,
                            run_index,
                            "ok",
                            text=text,
                            wall_ms=wall_ms,
                        )
                    )
                except BackendError as exc:
                    samples.append(
                        BenchmarkSample(
                            model,
                            fixture.id,
                            fixture.content_hash,
                            target_variant,
                            run_index,
                            "error",
                            wall_ms=(self.clock() - started) * 1000,
                            error_code=exc.code,
                        )
                    )
                except (KeyboardInterrupt, InterruptedError):
                    interrupted = True
                    break
                except Exception as exc:
                    samples.append(
                        BenchmarkSample(
                            model,
                            fixture.id,
                            fixture.content_hash,
                            target_variant,
                            run_index,
                            "error",
                            wall_ms=(self.clock() - started) * 1000,
                            error_code=type(exc).__name__,
                        )
                    )
            if interrupted:
                break
        return BenchmarkResult(tuple(samples), interrupted)
