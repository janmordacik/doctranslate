"""Conservative retention and cleanup for translation run artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path
import time
from typing import Any

from .filename_policy import generated_sidecar


# These files are reproducible run metadata, not user documents. PDF and HTML
# files are deliberately absent: cleanup must never remove user-facing output.
SIDECAR_SUFFIXES = (
    ".translations.json",
    ".performance.json",
    ".run-error.json",
    ".ollama-error.json",
    ".plan.json",
    ".performance.md",
    ".run.log",
)
TEMP_FILE_PATTERNS = ("*.tmp", "*.tmp.pdf", "*.tmp.json")
TEMP_DIRECTORY_PATTERNS = ("root-pycache", "worker-smoke-*")
DEFAULT_MAX_SIDECAR_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_SIDECAR_TOTAL_BYTES = 250 * 1024 * 1024


@dataclass(frozen=True)
class RetentionPolicy:
    """Retention defaults for reproducible but bounded work directories."""

    sidecar_days: int = 30
    temporary_hours: int = 24
    keep_latest_sidecar_sets: int = 2
    max_sidecar_bytes: int = DEFAULT_MAX_SIDECAR_BYTES
    max_sidecar_total_bytes: int = DEFAULT_MAX_SIDECAR_TOTAL_BYTES

    def __post_init__(self) -> None:
        if self.sidecar_days < 0:
            raise ValueError("sidecar_days must not be negative")
        if self.temporary_hours < 0:
            raise ValueError("temporary_hours must not be negative")
        if self.keep_latest_sidecar_sets < 0:
            raise ValueError("keep_latest_sidecar_sets must not be negative")
        if self.max_sidecar_bytes <= 0:
            raise ValueError("max_sidecar_bytes must be positive")
        if self.max_sidecar_total_bytes <= 0:
            raise ValueError("max_sidecar_total_bytes must be positive")


def _sidecar_base(name: str) -> str | None:
    for suffix in sorted(SIDECAR_SUFFIXES, key=len, reverse=True):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _safe_path(workdir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        path = Path(value).expanduser().resolve()
        workdir = workdir.resolve()
        path.relative_to(workdir)
    except (OSError, RuntimeError, ValueError):
        return None
    return path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def protected_paths(workdir: Path, queue_path: Path | None = None) -> set[Path]:
    """Return files that cleanup must not remove for queued jobs."""
    workdir = Path(workdir).resolve()
    queue_path = Path(queue_path or workdir / "queue.json").resolve()
    protected: set[Path] = {queue_path}
    queue = _read_json(queue_path)
    for item in queue.get("items", []):
        if not isinstance(item, dict) or item.get("kind") != "job":
            continue
        for key in ("input", "output", "html_file"):
            path = _safe_path(workdir, item.get(key))
            if path is not None:
                protected.add(path)
        # Active, paused and failed jobs need their restart and diagnostics
        # sidecars. A done job can be regenerated and is eligible for aging.
        if item.get("state") in {"prepared", "in_progress", "paused", "failed"}:
            output = _safe_path(workdir, item.get("output"))
            if output is not None:
                for suffix in SIDECAR_SUFFIXES:
                    protected.add(generated_sidecar(output, suffix).resolve())
    return protected


def _active_worker(workdir: Path) -> bool:
    # The lock is the authoritative singleton indicator. A stale lock is not
    # cleaned automatically because removing it is a separate safety action.
    return (workdir / "worker.lock").exists()


def cleanup_workdir(
    workdir: Path,
    queue_path: Path | None = None,
    *,
    policy: RetentionPolicy | None = None,
    dry_run: bool = False,
    now: float | None = None,
) -> dict[str, Any]:
    """Remove aged reproducible artifacts without touching documents.

    The operation is intentionally a no-op while ``worker.lock`` exists.
    Only known sidecars, temporary files and empty test directories are
    candidates. The returned report is JSON-serializable for event logging.
    """
    workdir = Path(workdir).expanduser().resolve()
    policy = policy or RetentionPolicy()
    now = time.time() if now is None else now
    report: dict[str, Any] = {
        "workdir": str(workdir),
        "dry_run": dry_run,
        "active_worker": _active_worker(workdir),
        "removed": [],
        "skipped": [],
        "oversized": [],
        "sidecar_bytes_before": 0,
        "sidecar_bytes_after": 0,
        "sidecar_limit_exceeded": False,
    }
    if report["active_worker"]:
        report["skipped"].append("worker is running")
        return report
    try:
        entries = list(workdir.iterdir())
    except OSError as exc:
        report["skipped"].append(f"cannot list workdir: {exc}")
        return report

    protected = protected_paths(workdir, queue_path)
    sidecars: dict[str, list[Path]] = {}
    for path in entries:
        if not path.is_file():
            continue
        base = _sidecar_base(path.name)
        if base is not None:
            sidecars.setdefault(base, []).append(path)

    sidecar_sizes: dict[Path, int] = {}
    sidecar_mtimes: dict[Path, float] = {}
    for paths in sidecars.values():
        for path in paths:
            try:
                stat = path.stat()
            except OSError:
                continue
            sidecar_sizes[path] = stat.st_size
            sidecar_mtimes[path] = stat.st_mtime
    latest_bases = sorted(
        sidecars,
        key=lambda base: max((sidecar_mtimes.get(path, 0) for path in sidecars[base]), default=0),
        reverse=True,
    )[: policy.keep_latest_sidecar_sets]
    sidecar_bytes_before = sum(sidecar_sizes.values())
    report["sidecar_bytes_before"] = sidecar_bytes_before
    report["oversized"] = [
        str(path) for path, size in sidecar_sizes.items()
        if size > policy.max_sidecar_bytes
    ]
    sidecar_cutoff = now - policy.sidecar_days * 86400
    temporary_cutoff = now - policy.temporary_hours * 3600

    def remove(path: Path) -> None:
        if path in removed_paths:
            return
        if path in protected:
            report["skipped"].append(f"protected: {path.name}")
            return
        if dry_run:
            report["removed"].append(str(path))
            removed_paths.add(path)
            return
        try:
            path.unlink()
            report["removed"].append(str(path))
            removed_paths.add(path)
        except OSError as exc:
            report["skipped"].append(f"{path.name}: {exc}")

    removed_paths: set[Path] = set()
    for base, paths in sidecars.items():
        if base in latest_bases:
            continue
        for path in paths:
            try:
                old = sidecar_mtimes.get(path, path.stat().st_mtime) < sidecar_cutoff
            except OSError:
                continue
            oversized = sidecar_sizes.get(path, 0) > policy.max_sidecar_bytes
            if old or oversized:
                remove(path)

    # If old/oversized artifacts still exceed the aggregate budget, discard
    # the oldest unprotected non-latest sidecars first. Never truncate a file:
    # a translation cache remains either complete or preserved for recovery.
    remaining = [
        (path, sidecar_sizes[path], sidecar_mtimes.get(path, 0), base)
        for base, paths in sidecars.items()
        if base not in latest_bases
        for path in paths
        if path in sidecar_sizes and path not in removed_paths and path not in protected
    ]
    remaining_bytes = sum(size for _path, size, _mtime, _base in remaining)
    if remaining_bytes > policy.max_sidecar_total_bytes:
        for path, size, _mtime, _base in sorted(remaining, key=lambda item: item[2]):
            if remaining_bytes <= policy.max_sidecar_total_bytes:
                break
            remove(path)
            if path in removed_paths:
                remaining_bytes -= size

    for path in entries:
        if not path.is_file() or not any(fnmatch.fnmatch(path.name, pattern) for pattern in TEMP_FILE_PATTERNS):
            continue
        try:
            if path.stat().st_mtime < temporary_cutoff:
                remove(path)
        except OSError:
            continue

    for path in entries:
        if not path.is_dir() or not any(fnmatch.fnmatch(path.name, pattern) for pattern in TEMP_DIRECTORY_PATTERNS):
            continue
        try:
            if path.stat().st_mtime >= temporary_cutoff or any(path.iterdir()):
                continue
            if dry_run:
                report["removed"].append(str(path))
            else:
                path.rmdir()
                report["removed"].append(str(path))
        except OSError as exc:
            report["skipped"].append(f"{path.name}: {exc}")
    after_paths = [path for path in sidecar_sizes if path not in removed_paths]
    report["sidecar_bytes_after"] = sum(sidecar_sizes[path] for path in after_paths)
    report["sidecar_limit_exceeded"] = (
        report["sidecar_bytes_after"] > policy.max_sidecar_total_bytes
        or any(sidecar_sizes[path] > policy.max_sidecar_bytes for path in after_paths)
    )
    report["removed_count"] = len(report["removed"])
    return report


def cleanup_queue_workdirs(
    queue_path: Path,
    *,
    policy: RetentionPolicy | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Clean the queue directory and directories referenced by its jobs."""
    queue_path = Path(queue_path).expanduser().resolve()
    root = queue_path.parent
    policy = policy or RetentionPolicy()
    if _active_worker(root):
        return [cleanup_workdir(root, queue_path, policy=policy, dry_run=dry_run)]
    locations = {root}
    queue = _read_json(queue_path)
    for item in queue.get("items", []):
        if not isinstance(item, dict) or item.get("kind") != "job":
            continue
        for key in ("input", "output", "html_file"):
            path = item.get(key)
            if isinstance(path, str) and path.strip():
                try:
                    locations.add(Path(path).expanduser().resolve().parent)
                except (OSError, RuntimeError, ValueError):
                    continue
    return [
        cleanup_workdir(location, queue_path, policy=policy, dry_run=dry_run)
        for location in sorted(locations, key=str.casefold)
    ]
