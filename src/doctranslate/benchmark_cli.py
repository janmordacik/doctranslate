"""Command-line wrapper around the provider-neutral benchmark runner."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .ai import BenchmarkRunner, load_builtin_fixtures
from .ai import StyleLibrary
from .ai.ollama import OllamaBackend
from .ai.contracts import BackendError


def run_benchmark(
    models: list[str],
    *,
    ollama_url: str,
    report_path: Path | None = None,
    target_variant: str = "auto",
) -> int:
    """Run the built-in en→cs fixture and write a JSON report.

    An empty model list means discovery from the configured Ollama endpoint.
    No model is downloaded by this command.
    """

    discovery = OllamaBackend("benchmark-discovery", base_url=ollama_url)
    if not models:
        try:
            models = list(discovery.list_models())
        except Exception as exc:
            print(f"Benchmark cannot discover Ollama models: {exc}", file=sys.stderr)
            return 1
    models = list(dict.fromkeys(model.strip() for model in models if model.strip()))
    if not models:
        print("Benchmark found no usable models.", file=sys.stderr)
        return 1

    fixture = load_builtin_fixtures()[0]
    try:
        target_variant = StyleLibrary().resolve_variant(target_variant, fixture.target_language)
    except ValueError as exc:
        print(f"Benchmark has invalid style variant: {exc}", file=sys.stderr)
        return 2
    runner = BenchmarkRunner(
        lambda model: OllamaBackend(model, base_url=ollama_url),
        repeats=4,
    )
    result = runner.run(models, fixture, target_variant=target_variant)
    for model in models:
        samples = [sample for sample in result.samples if sample.model == model]
        ok = [sample for sample in samples if sample.status == "ok"]
        status = "OK" if ok else ("SKIP" if samples and samples[0].status == "skip" else "FAIL")
        first = next((sample.wall_ms for sample in ok if sample.run_index == 0), None)
        warm = result.warm_median_ms(model)
        print(
            f"{model} | {status} | FIRST_REQUEST={first if first is not None else '-'} ms "
            f"| WARM_MEDIAN={warm if warm is not None else '-'} ms"
        )
        for sample in ok:
            print(f"  run={sample.run_index} {sample.wall_ms:.1f} ms {sample.text}")

    report = {
        "fixture": {
            "id": fixture.id,
            "version": fixture.version,
            "content_hash": fixture.content_hash,
            "source_language": fixture.source_language,
            "target_language": fixture.target_language,
            "target_variant": target_variant,
            "source": fixture.source,
            "references": list(fixture.references),
        },
        "models": models,
        "interrupted": result.interrupted,
        "samples": [sample.__dict__ for sample in result.samples],
    }
    report_path = report_path or Path.cwd() / (
        "benchmark-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Benchmark report: {report_path}")
    return 0 if any(sample.status == "ok" for sample in result.samples) else 1
