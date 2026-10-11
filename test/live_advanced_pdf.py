"""Opt-in live integration smoke test for the advanced Ollama PDF path.

The script intentionally is not collected by pytest.  It creates an isolated
queue, starts the real worker, waits for one advanced translation job and
validates both the translated XHTML and the rendered PDF.  It never removes
the input PDF or files outside its own output directory.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from doctranslate.observability import queue_log_path
from doctranslate.queue_app import QueueStore, WorkerController, make_job


class LiveTestError(RuntimeError):
    """Describe a failed preflight or live worker attempt."""


def utc_now() -> str:
    """Return an ISO timestamp suitable for the test report."""
    return datetime.now(timezone.utc).isoformat()


def write_record(path: Path, event: str, **fields: object) -> None:
    """Append one structured test-run record without hiding the test error."""
    record = {"time_utc": utc_now(), "event": event, **fields}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def read_json(path: Path) -> dict:
    """Read one JSON object, returning an empty object for a missing file."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def api_json(base_url: str, path: str) -> dict:
    """Read one Ollama API object with a short preflight timeout."""
    request = Request(base_url.rstrip("/") + path, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=5) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, HTTPError, URLError) as exc:
        raise LiveTestError(f"Ollama API {path} is unavailable: {exc}") from exc
    if not isinstance(value, dict):
        raise LiveTestError(f"Ollama API {path} returned a non-object response")
    return value


def model_record(payload: dict, model: str) -> dict | None:
    """Find the exact model record returned by Ollama tags or ps."""
    models = payload.get("models")
    if not isinstance(models, list):
        return None
    return next(
        (
            item for item in models
            if isinstance(item, dict) and item.get("name", item.get("model")) == model
        ),
        None,
    )


def remove_test_file(path: Path, removed: list[str]) -> None:
    """Remove one explicitly owned test artifact and record the removal."""
    if path.is_file() or path.is_symlink():
        path.unlink()
        removed.append(str(path))


def cleanup_attempt(run_dir: Path, output: Path, html: Path, queue: Path) -> list[str]:
    """Remove only artifacts produced by this isolated live test."""
    removed: list[str] = []
    names = {
        output,
        html,
        output.with_suffix(".plan.json"),
        output.with_suffix(".translations.json"),
        output.with_suffix(".run.log"),
        output.with_name(output.name + ".advanced.checkpoint.json"),
        output.with_name(output.name + ".advanced.glossary.json"),
        queue,
        queue.with_suffix(".bak"),
        queue.with_suffix(".lock"),
        queue.with_name("worker-state.json"),
        queue.with_name("worker.lock"),
        queue.with_name("worker.log"),
        queue_log_path(queue),
        run_dir / "test.log",
        run_dir / "result.json",
    }
    for path in names:
        remove_test_file(path, removed)
    return removed


def preflight(
    source: Path,
    run_dir: Path,
    model: str,
    ollama_url: str,
    minimum_free_bytes: int,
    managed_ollama: bool,
) -> dict:
    """Verify inputs, disk space, Ollama API and the requested model."""
    if not source.is_file():
        raise LiveTestError(f"Input PDF does not exist: {source}")
    if source.suffix.lower() != ".pdf":
        raise LiveTestError(f"Input must be a PDF: {source}")
    run_dir.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(run_dir).free
    if free < minimum_free_bytes:
        raise LiveTestError(
            f"Insufficient free space in {run_dir}: {free} bytes, "
            f"required at least {minimum_free_bytes}"
        )
    tags = api_json(ollama_url, "/api/tags")
    record = model_record(tags, model)
    if record is None:
        available = [
            item.get("name", item.get("model"))
            for item in tags.get("models", [])
            if isinstance(item, dict)
        ]
        raise LiveTestError(f"Ollama model {model!r} is unavailable; found {available}")
    if managed_ollama and not shutil.which("ollama"):
        raise LiveTestError("Managed Ollama test requested, but executable 'ollama' was not found")
    if managed_ollama and not os.environ.get("OLLAMA_MODELS"):
        raise LiveTestError(
            "Managed Ollama test requires OLLAMA_MODELS so the worker uses the intended model store"
        )
    return {
        "model": model,
        "model_size": record.get("size"),
        "model_details": record.get("details"),
        "free_bytes": free,
        "managed_ollama": managed_ollama,
    }


def wait_for_job(
    store: QueueStore,
    controller: WorkerController,
    job_id: str,
    timeout_seconds: int,
    log_path: Path,
) -> dict:
    """Poll the isolated queue until the job reaches a terminal state."""
    started = time.monotonic()
    terminal = {"done", "failed", "paused"}
    while time.monotonic() - started < timeout_seconds:
        jobs = {job.get("id"): job for job in store.jobs()}
        job = jobs.get(job_id, {})
        state = job.get("state")
        if state in terminal:
            while controller.running() and time.monotonic() - started < timeout_seconds:
                time.sleep(0.5)
            return job
        write_record(log_path, "test.poll", job_id=job_id, state=state)
        time.sleep(2)
    controller.stop()
    raise LiveTestError(f"Live job did not finish within {timeout_seconds} seconds")


def validate_outputs(output: Path, html: Path) -> dict:
    """Validate non-empty XHTML and a readable PDF with at least one page."""
    if not html.is_file() or html.stat().st_size == 0:
        raise LiveTestError(f"Translated XHTML was not created: {html}")
    if not output.is_file() or output.stat().st_size == 0:
        raise LiveTestError(f"Translated PDF was not created: {output}")
    try:
        import fitz

        with fitz.open(output) as document:
            pages = len(document)
    except Exception as exc:
        raise LiveTestError(f"Translated PDF cannot be opened: {output}: {exc}") from exc
    if pages < 1:
        raise LiveTestError(f"Translated PDF has no pages: {output}")
    return {"html_bytes": html.stat().st_size, "pdf_bytes": output.stat().st_size, "pdf_pages": pages}


def run(args: argparse.Namespace) -> int:
    """Run one isolated advanced translation attempt and write its report."""
    source = args.input.resolve()
    run_dir = args.run_dir.resolve()
    output = (run_dir / args.output_name).resolve()
    html = (run_dir / args.html_name).resolve()
    queue = (run_dir / args.queue_name).resolve()
    test_log = run_dir / "test.log"
    removed = cleanup_attempt(run_dir, output, html, queue)
    write_record(test_log, "test.started", source=source, model=args.model, removed=removed)
    try:
        capability = preflight(
            source, run_dir, args.model, args.ollama_url,
            args.minimum_free_bytes, args.managed_ollama,
        )
        os.environ["TRANSLATE_OLLAMA_URL"] = args.ollama_url
        job = make_job(
            source,
            output,
            inlang="en",
            outlang="cs",
            model=args.model,
            provider="ollama",
            phase="both",
            translator_id="advanced",
            html_file=html,
            translator_options={
                "manage_ollama": args.managed_ollama,
                "request_timeout": args.request_timeout,
            },
        )
        store = QueueStore(queue)
        store.append_job(job)
        controller = WorkerController(queue)
        controller.start()
        result = wait_for_job(store, controller, job["id"], args.timeout_seconds, test_log)
        event_log = queue_log_path(queue)
        if result.get("state") != "done":
            raise LiveTestError(
                f"Advanced job ended in state {result.get('state')}: {result.get('error')}"
            )
        artifacts = validate_outputs(output, html)
        report = {
            "status": "passed",
            "finished_at": utc_now(),
            "job": result,
            "capability": capability,
            "artifacts": artifacts,
            "queue_events": str(event_log),
            "run_log": str(output.with_suffix(".run.log")),
            "worker_log": str(queue.with_name("worker.log")),
        }
        write_record(test_log, "test.completed", **report)
        (run_dir / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        report = {
            "status": "failed",
            "finished_at": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "queue": str(queue),
            "test_log": str(test_log),
            "worker_log": str(queue.with_name("worker.log")),
            "run_log": str(output.with_suffix(".run.log")),
        }
        write_record(test_log, "test.failed", **report)
        (run_dir / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit live-test command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "test/mock/sample-en.pdf")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "tmp/advanced-live")
    parser.add_argument("--model", default="translategemma:4b")
    parser.add_argument("--ollama-url", default=os.environ.get("TRANSLATE_OLLAMA_URL", "http://127.0.0.1:11434"))
    parser.add_argument("--output-name", default="translated.pdf")
    parser.add_argument("--html-name", default="translated.html")
    parser.add_argument("--queue-name", default="queue.json")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--request-timeout", type=int, default=1800)
    parser.add_argument("--minimum-free-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--managed-ollama", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
