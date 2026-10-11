"""Persistent queue worker for the file-based translation protocol."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback

from .queue_app import (
    FileLock,
    QueueStore,
    StorageError,
    discover_translation_html,
    utc_now,
)
from .retention import cleanup_queue_workdirs

PREVIEW_UPDATE_INTERVAL_SECONDS = 10.0
PREVIEW_TERMINAL_STAGES = frozenset({"translated", "error", "stopped", "done", "failed"})


@dataclass(frozen=True)
class JobOptions:
    """Immutable run inputs copied from one queue job."""

    input: str
    output: str
    inlang: str
    outlang: str
    phase: str
    html_file: str | None
    model: str | None
    provider: str
    profile: str | None
    input_format: str | None
    output_format: str | None
    first_page: int
    last_page: int | None
    target_variant: str = "auto"
    translator_id: str = "basic"
    translator_options: dict = field(default_factory=dict)

    @classmethod
    def from_job(cls, job: dict) -> "JobOptions":
        return cls(
            input=job["input"],
            output=job["output"],
            inlang=job.get("inlang", "en"),
            outlang=job.get("outlang", "cs"),
            phase=job.get("phase", "both"),
            html_file=job.get("html_file"),
            model=job.get("model"),
            provider=job.get("provider", "ollama"),
            profile=job.get("profile"),
            input_format=job.get("input_format"),
            output_format=job.get("output_format"),
            first_page=job.get("first_page", 1),
            last_page=job.get("last_page"),
            target_variant=job.get("target_variant", "auto"),
            translator_id=job.get("translator_id", "basic"),
            translator_options=copy.deepcopy(job.get("translator_options", {})),
        )


class Worker:
    """Singleton worker that polls JSON control state between safe work boundaries."""

    def __init__(self, queue_path: Path):
        self.store = QueueStore(queue_path)
        self.logger = self.store.logger
        self.cancel_event = threading.Event()
        self.current_job_id: str | None = None
        self.runtime_state = "starting"
        self.activity = "starting"
        self.activity_fields: dict[str, object] = {}
        self.last_preview_at: float | None = None
        self.last_preview_job_id: str | None = None
        self.state_lock = threading.RLock()
        self.heartbeat_stop = threading.Event()
        self.heartbeat_thread: threading.Thread | None = None
        self.control_monitor_stop = threading.Event()
        self.control_monitor_thread: threading.Thread | None = None
        self.state_path = self.store.path.with_name("worker-state.json")
        self.worker_lock = self.store.path.with_name("worker.lock")

    def write_state(self, state: str, emit_event: bool = True, **extra) -> None:
        """Persist diagnostic state and mirror it as a structured event."""
        payload = {
            "pid": os.getpid(),
            "state": state,
            "heartbeat": utc_now(),
            "job_id": self.current_job_id,
            "activity": self.activity,
            **self.activity_fields,
            **extra,
        }
        temporary = self.state_path.with_name(self.state_path.name + ".tmp")
        with self.state_lock:
            self.runtime_state = state
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temporary, self.state_path)
                if emit_event:
                    self.logger.event("worker.state", state=state, job_id=self.current_job_id, **extra)
            except (OSError, StorageError) as exc:
                # Runtime state is diagnostic; a full or read-only disk must not
                # hide the original translation error or crash the worker loop.
                print(f"WARNING: cannot write worker state {self.state_path}: {exc}", file=sys.stderr)
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def set_activity(self, activity: str, **fields: object) -> None:
        """Publish human-readable activity without changing job state."""
        self.activity = activity
        self.activity_fields = dict(fields)
        self.write_state(self.runtime_state, emit_event=False)

    def report_progress(
        self,
        completed: int,
        total: int,
        *,
        unit: str = "pages",
        current_page: int | None = None,
    ) -> None:
        """Persist a bounded transient progress snapshot for GUI and CLI."""
        total = max(int(total), 1)
        completed = max(0, min(int(completed), total))
        fields: dict[str, object] = {
            "progress": completed / total,
            "completed": completed,
            "total": total,
            "unit": unit,
        }
        if current_page is not None:
            fields["current_page"] = int(current_page)
        self.activity_fields.update(fields)
        self.write_state(self.runtime_state, emit_event=False)

    def publish_preview(self, preview: dict[str, object]) -> None:
        """Publish the latest bounded translation preview in runtime state."""
        value = dict(preview)
        job_id = self.current_job_id
        stage = str(value.get("stage", ""))
        now = time.monotonic()
        new_job = job_id != self.last_preview_job_id
        if (
            not new_job
            and stage not in PREVIEW_TERMINAL_STAGES
            and self.last_preview_at is not None
            and now - self.last_preview_at < PREVIEW_UPDATE_INTERVAL_SECONDS
        ):
            return
        value["job_id"] = job_id
        self.activity_fields["preview"] = value
        self.last_preview_at = now
        self.last_preview_job_id = job_id
        self.write_state(self.runtime_state, emit_event=False)

    def _heartbeat(self) -> None:
        while not self.heartbeat_stop.wait(1.0):
            if self.current_job_id is not None:
                self.write_state(self.runtime_state, emit_event=False)

    def start_heartbeat(self) -> None:
        self.heartbeat_stop.clear()
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat, name="worker-heartbeat", daemon=True
        )
        self.heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        self.heartbeat_stop.set()
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.join(timeout=2)
            self.heartbeat_thread = None

    def start_control_monitor(self) -> None:
        """Watch stop while an AI request is blocking the main thread."""
        self.control_monitor_stop.clear()
        self.control_monitor_thread = threading.Thread(
            target=self._control_monitor,
            name="worker-control-monitor",
            daemon=True,
        )
        self.control_monitor_thread.start()

    def _control_monitor(self) -> None:
        announced = False
        while not self.control_monitor_stop.wait(0.2):
            try:
                command = self.control().get("command")
            except (OSError, ValueError, RuntimeError, KeyError, IndexError):
                continue
            current = next(
                (item for item in self.store.jobs() if item.get("id") == self.current_job_id),
                None,
            )
            invalidated = current is None or current.get("state") != "in_progress"
            if command == "stop" or invalidated:
                self.cancel_event.set()
                if not announced:
                    self.logger.event(
                        "worker.job.invalidation_observed" if invalidated else "worker.stop.ai_observed",
                        job_id=self.current_job_id,
                        reason=("deleted" if current is None else current.get("state"))
                        if invalidated else "stop",
                    )
                    announced = True
                return

    def stop_control_monitor(self) -> None:
        self.control_monitor_stop.set()
        if self.control_monitor_thread is not None:
            self.control_monitor_thread.join(timeout=2)
            self.control_monitor_thread = None

    def choose_job(self) -> dict | None:
        """Choose the first resumable job, then the first prepared job."""
        jobs = self.store.jobs()
        # List order is the only prepared-job priority; an interrupted job
        # always resumes first so a restart cannot strand partial work.
        active = [job for job in jobs if job.get("state") == "in_progress"]
        prepared = [job for job in jobs if job.get("state") == "prepared"]
        return (active + prepared)[0] if active or prepared else None

    def control(self) -> dict:
        return self.store.load()["items"][0]

    def after_batch(self) -> None:
        """Poll control only at a safe batch boundary, never mid-request."""
        progress_fields = {
            key: self.activity_fields[key]
            for key in ("progress", "completed", "total", "unit", "current_page", "preview")
            if key in self.activity_fields
        }
        self.set_activity("polling", **progress_fields)
        self.write_state("polling")
        control = self.control()
        if control.get("command") == "stop":
            self.cancel_event.set()
            self.logger.event("worker.stop.observed", job_id=self.current_job_id)
        if self.current_job_id:
            job = next(
                (item for item in self.store.jobs() if item.get("id") == self.current_job_id),
                None,
            )
            if job and job.get("state") == "paused":
                self.cancel_event.set()
                self.logger.event("worker.pause.observed", job_id=self.current_job_id)

    def mark_job(self, job_id: str, state: str, **changes) -> None:
        """Persist a state transition while retaining unrelated job fields."""
        self.store.update_job(job_id, state=state, **changes)

    def run_job(self, job: dict) -> None:
        """Run one job and preserve restart semantics for cancellation or failure."""
        from . import translate

        options = JobOptions.from_job(job)
        self.current_job_id = job["id"]
        self.cancel_event.clear()
        html_file = options.html_file
        if options.phase == "pdf" and not html_file:
            html_file = discover_translation_html(
                options.input,
                options.output,
                inlang=options.inlang,
                outlang=options.outlang,
            )
            if html_file:
                self.logger.event(
                    "worker.html.discovered",
                    job_id=self.current_job_id,
                    html_file=str(html_file),
                )
        self.set_activity(
            "preparing",
            phase=options.phase,
            html_file=str(html_file) if html_file else None,
            progress=0.0,
            completed=0,
            total=None,
            unit="pages",
        )
        self.logger.event(
            "worker.job.started",
            job_id=self.current_job_id,
            model=options.model,
            phase=options.phase,
        )
        self.mark_job(
            self.current_job_id,
            "in_progress",
            error=None,
            started_at=job.get("started_at") or utc_now(),
        )
        self.write_state("in_progress")
        translate.QUEUE_HOOK = self.after_batch
        translate.PROGRESS_HOOK = self.report_progress
        translate.PREVIEW_HOOK = self.publish_preview
        self.start_control_monitor()
        try:
            if options.phase == "pdf" and not html_file:
                raise RuntimeError(
                    "PDF phase requires a complete translated HTML file; "
                    "specify html_file or place matching HTML beside the input/output PDF"
                )
            self.set_activity(
                "translating" if options.phase in ("html", "both") else "typesetting",
                phase=options.phase,
                html_file=str(html_file) if html_file else None,
                progress=0.0,
                completed=0,
                total=None,
                unit="pages",
            )
            translate.TARGET_VARIANT = options.target_variant or "auto"
            translate.configure(
                options.input,
                options.output,
                options.inlang,
                options.outlang,
            )
            translate.MODEL = options.model or translate.DEFAULT_MODEL
            translate.PROVIDER_ID = options.provider or "ollama"
            translate.PROFILE_ID = options.profile
            translate.INPUT_FORMAT = options.input_format or "pdf"
            translate.OUTPUT_FORMAT = options.output_format or "pdf"
            translate.FIRST_PAGE = options.first_page
            translate.LAST_PAGE = options.last_page
            translate.configure_phases(options.phase, html_file)
            translate.main(self.cancel_event)
        except KeyboardInterrupt:
            # Stop keeps in_progress for restart; pause keeps the explicit paused state.
            current = next(
                (item for item in self.store.jobs() if item.get("id") == self.current_job_id),
                None,
            )
            if current and current.get("state") == "in_progress":
                self.mark_job(self.current_job_id, "in_progress")
            self.write_state("paused" if current and current.get("state") == "paused" else "stopped")
            raise
        except Exception as exc:
            self.logger.event(
                "worker.job.failed",
                job_id=self.current_job_id,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            self.mark_job(
                self.current_job_id,
                "failed",
                error=f"{type(exc).__name__}: {exc}",
                traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
            self.write_state("failed", error=str(exc))
        else:
            total = self.activity_fields.get("total")
            if not isinstance(total, int) or total < 1:
                total = 1
            self.report_progress(total, total, unit=str(self.activity_fields.get("unit") or "pages"))
            self.mark_job(self.current_job_id, "done", progress=1.0, error=None)
            self.logger.event("worker.job.completed", job_id=self.current_job_id)
            self.write_state("job_done")
        finally:
            self.stop_control_monitor()
            translate.QUEUE_HOOK = None
            translate.PROGRESS_HOOK = None
            translate.PREVIEW_HOOK = None
            self.current_job_id = None

    def run(self) -> int:
        """Acquire the singleton lock, process jobs in order, then release it."""
        lock = FileLock(self.worker_lock, timeout=0)
        try:
            lock.acquire()
        except (FileExistsError, TimeoutError):
            self.logger.event("worker.start.skipped", reason="singleton_locked")
            return 10
        try:
            self.logger.event("worker.run.started", pid=os.getpid())
            self.start_heartbeat()
            self.write_state("starting")
            while True:
                if self.control().get("command") == "stop":
                    self.store.consume_stop()
                    break
                job = self.choose_job()
                if job is None:
                    break
                try:
                    self.run_job(job)
                except KeyboardInterrupt:
                    command = self.control().get("command")
                    if command == "stop":
                        self.store.consume_stop()
                        break
                    # Paused job remains in the queue; wait for a later Start.
                    break
                except Exception as exc:
                    print(
                        f"ERROR: worker could not process job {job.get('id')}: "
                        f"{type(exc).__name__}: {exc}",
                        file=sys.stderr,
                    )
                    self.write_state("failed", error=str(exc))
                    return 2
            self.write_state("stopped")
            self.logger.event("worker.run.stopped")
            return 0
        finally:
            self.stop_heartbeat()
            lock.release()
            try:
                self.state_path.unlink()
            except FileNotFoundError:
                pass
            try:
                reports = cleanup_queue_workdirs(self.store.path)
                self.logger.event("retention.cleanup", reports=reports)
            except Exception as exc:
                # Retention must never turn a completed worker run into a
                # failed run. Keep the failure visible in the event log.
                self.logger.event("retention.cleanup.failed", error=str(exc))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    args = parser.parse_args(argv)
    return Worker(args.queue).run()


if __name__ == "__main__":
    raise SystemExit(main())
