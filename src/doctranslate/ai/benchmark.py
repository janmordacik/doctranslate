"""Provider-neutral benchmark runner for deterministic translation fixtures."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
import threading
import time
from typing import Any, Callable, Iterable, Mapping

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



@dataclass(frozen=True)
class EngineBenchmarkSample:
    """One comparable run of a translation engine over one unique fixture."""

    engine_id: str
    fixture_id: str
    fixture_hash: str
    run_index: int
    status: str
    text: str = ""
    wall_ms: float | None = None
    token_count: int | None = None
    repair_count: int | None = None
    quality: str = "unknown"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None


@dataclass(frozen=True)
class EngineBenchmarkResult:
    samples: tuple[EngineBenchmarkSample, ...]

    def jsonl(self) -> str:
        import json

        return "".join(
            json.dumps(sample.__dict__, ensure_ascii=False, sort_keys=True) + "\n"
            for sample in self.samples
        )


class EngineBenchmarkRunner:
    """Compare injected basic/advanced callables without live provider assumptions."""

    def __init__(
        self,
        engines: Mapping[str, Callable[[BenchmarkFixture], object]],
        *,
        repeats: int = 1,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if repeats < 1:
            raise ValueError("repeats must be positive")
        if not engines:
            raise ValueError("at least one engine is required")
        self.engines = dict(engines)
        self.repeats = repeats
        self.clock = clock

    def run(self, fixture: BenchmarkFixture) -> EngineBenchmarkResult:
        samples: list[EngineBenchmarkSample] = []
        for engine_id, runner in self.engines.items():
            for run_index in range(self.repeats):
                started = self.clock()
                try:
                    result = runner(fixture)
                    wall_ms = (self.clock() - started) * 1000
                    text, token_count, repairs, quality, metadata = self._extract(result)
                    result_status = getattr(result, "status", "done")
                    status = "ok" if result_status in {"done", None} else "unresolved"
                    samples.append(
                        EngineBenchmarkSample(
                            engine_id,
                            fixture.id,
                            fixture.content_hash,
                            run_index,
                            status,
                            text=text,
                            wall_ms=wall_ms,
                            token_count=token_count,
                            repair_count=repairs,
                            quality=quality,
                            metadata=metadata,
                            error_code=None if status == "ok" else str(
                                getattr(result, "reason", result_status)
                            ),
                        )
                    )
                except Exception as exc:
                    samples.append(
                        EngineBenchmarkSample(
                            engine_id,
                            fixture.id,
                            fixture.content_hash,
                            run_index,
                            "error",
                            wall_ms=(self.clock() - started) * 1000,
                            error_code=type(exc).__name__,
                        )
                    )
        return EngineBenchmarkResult(tuple(samples))

    @staticmethod
    def _extract(result: object) -> tuple[str, int | None, int | None, str, Mapping[str, Any]]:
        if isinstance(result, str):
            return result, None, None, "unknown", {}
        document = getattr(result, "document", None)
        blocks = getattr(document, "blocks", ()) if document is not None else ()
        text = "\n\n".join(
            str(getattr(block, "text", "")) for block in blocks
        ) if blocks else str(getattr(result, "text", ""))
        metadata: dict[str, Any] = {}
        session_status = getattr(result, "status", None)
        if session_status is not None:
            metadata = {
                "session_status": session_status,
                "turns": getattr(result, "turns", None),
                "tool_calls": getattr(result, "tool_calls", None),
                "revisions": getattr(result, "revisions", None),
                "reason": getattr(result, "reason", ""),
            }
            text = str(getattr(result, "translated_text", text))
        metrics = getattr(result, "metrics", None)
        token_count = None
        repairs = None
        if metrics is not None:
            metadata = {
                "translator_id": getattr(metrics, "translator_id", None),
                "translator_revision": getattr(metrics, "translator_revision", None),
                "batches": getattr(metrics, "batches", None),
                "segments": getattr(metrics, "segments", None),
                "ai_calls": getattr(metrics, "ai_calls", None),
                "resumed": getattr(metrics, "resumed", None),
                "prompt_tokens": getattr(metrics, "prompt_tokens", None),
                "output_tokens": getattr(metrics, "output_tokens", None),
            }
            accounting = getattr(metrics, "token_accounting", {})
            if isinstance(accounting, Mapping):
                numeric = [value for value in accounting.values() if isinstance(value, int)]
                token_count = sum(numeric) if numeric else None
                metadata["token_accounting"] = dict(accounting)
            prompt_tokens = metadata["prompt_tokens"]
            output_tokens = metadata["output_tokens"]
            if isinstance(prompt_tokens, int) and isinstance(output_tokens, int):
                token_count = prompt_tokens + output_tokens
            repairs = getattr(metrics, "revisions", None)
        warnings = tuple(getattr(result, "warnings", ()) or ())
        if session_status is not None and session_status != "done":
            quality = "unresolved"
        else:
            quality = "warnings" if warnings else ("ok" if text.strip() else "unknown")
        metadata["warnings"] = list(warnings)
        return text, token_count, repairs, quality, metadata


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
