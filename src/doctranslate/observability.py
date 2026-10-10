"""Small, dependency-free structured logging used by CLI, GUI and worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import threading
from typing import Any


@dataclass
class JsonEventLogger:
    """Append one JSON object per event without hiding the original operation.

    Logging is deliberately best-effort: a full or read-only disk must not turn
    a successful translation or queue update into a failed operation. The
    event schema remains stable across GUI, CLI, worker and translation runs.
    """

    path: Path
    echo: bool = False
    _locks: dict[Path, threading.Lock] = field(default_factory=dict, init=False, repr=False)

    def event(self, name: str, **fields: Any) -> bool:
        """Write an event and return whether it reached the log file."""
        record = {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "event": name,
            **fields,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # The per-instance lock protects threads in one process. File
            # append is intentionally short; queue locks are never held here.
            lock = self._locks.setdefault(self.path, threading.Lock())
            with lock:
                with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                    stream.flush()
            if self.echo:
                print("[trace] " + json.dumps(record, ensure_ascii=False, default=str), flush=True)
            return True
        except (OSError, TypeError, ValueError) as exc:
            # Diagnostics must never mask the operation being observed.
            if self.echo:
                print(f"[trace] logging failed: {exc}", file=sys.stderr, flush=True)
            return False


def queue_log_path(queue_path: Path) -> Path:
    """Return the stable event-log path next to a queue JSON file."""
    queue_path = Path(queue_path)
    return queue_path.with_name(queue_path.stem + ".events.log")
