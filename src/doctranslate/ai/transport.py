"""Minimal HTTP transports shared by provider plugins.

The Ollama backend uses SubprocessHttpTransport so a blocking local model
request is owned by a disposable child process. The queue worker can then
enforce a wall-clock deadline and cancel the request without leaving a stuck
urllib call in the supervisor process.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from threading import Event, Thread
from typing import Callable, Mapping
from urllib import error, request

from .contracts import BackendError


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: object


def _request_with_urllib(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] = (),
    payload: object | None = None,
    timeout: float | None = 120,
) -> HttpResponse:
    """Perform one blocking request in the current process."""
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=data, method=method, headers=dict(headers))
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            return HttpResponse(response.status, dict(response.headers), body)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"error": raw}
        return HttpResponse(exc.code, dict(exc.headers or {}), body)
    except (OSError, TimeoutError) as exc:
        raise BackendError("network_error", str(exc), retryable=True) from exc


class UrllibTransport:
    """Synchronous standard-library transport for short provider calls."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] = (),
        payload: object | None = None,
        timeout: float | None = 120,
    ) -> HttpResponse:
        return _request_with_urllib(
            method,
            url,
            headers=headers,
            payload=payload,
            timeout=timeout,
        )


class SubprocessHttpTransport:
    """Run one HTTP request in a killable child process.

    urllib has no portable way to interrupt a response read from another
    thread. The parent therefore polls the child, the cancellation event and
    a wall-clock deadline. Abort callbacks are used by Ollama to restart its
    worker-owned server after a timed out or cancelled request.
    """

    def __init__(
        self,
        *,
        cancel_event: Event | None = None,
        on_abort: Callable[[str], None] | None = None,
        poll_interval: float = 0.05,
    ) -> None:
        self.cancel_event = cancel_event
        self.on_abort = on_abort
        self.poll_interval = max(float(poll_interval), 0.01)
        self._process: subprocess.Popen[str] | None = None

    def bind_control(
        self,
        *,
        cancel_event: Event | None = None,
        on_abort: Callable[[str], None] | None = None,
    ) -> None:
        """Attach worker cancellation and provider-runtime callbacks."""
        self.cancel_event = cancel_event
        self.on_abort = on_abort

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] = (),
        payload: object | None = None,
        timeout: float | None = 120,
    ) -> HttpResponse:
        """Return a response or raise a typed cancellation/timeout error."""
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise BackendError("cancelled", "AI request cancelled", retryable=False)

        specification = json.dumps(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "payload": payload,
                "timeout": timeout,
            },
            ensure_ascii=False,
        )
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        environment = os.environ.copy()
        package_root = str(Path(__file__).resolve().parents[2])
        environment["PYTHONPATH"] = os.pathsep.join(
            value for value in (package_root, environment.get("PYTHONPATH", "")) if value
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "doctranslate.ai.transport", "--child"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags,
            env=environment,
        )
        self._process = process
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        def drain(stream, chunks: list[str]) -> None:
            """Drain a child pipe while the parent monitors cancellation."""
            try:
                chunks.append(stream.read())
            except (OSError, ValueError):
                # The process may close its pipe while the parent aborts it.
                pass

        readers = (
            Thread(target=drain, args=(process.stdout, stdout_chunks), daemon=True),
            Thread(target=drain, args=(process.stderr, stderr_chunks), daemon=True),
        )
        for reader in readers:
            reader.start()
        try:
            assert process.stdin is not None
            process.stdin.write(specification)
            process.stdin.close()
            deadline = (
                None
                if timeout is None or float(timeout) < 0
                else time.monotonic() + float(timeout)
            )
            while process.poll() is None:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self._terminate(process)
                    self._notify_abort("cancelled")
                    raise BackendError("cancelled", "AI request cancelled", retryable=False)
                if deadline is not None and time.monotonic() >= deadline:
                    self._terminate(process)
                    self._notify_abort("timeout")
                    raise BackendError(
                        "request_timeout",
                        f"AI request exceeded {float(timeout):g} seconds",
                        retryable=True,
                    )
                time.sleep(self.poll_interval)

        except (OSError, ValueError) as exc:
            self._terminate(process)
            raise BackendError("network_error", str(exc), retryable=True) from exc
        finally:
            if process.poll() is None:
                self._terminate(process)
            for reader in readers:
                reader.join(timeout=2)
            self._process = None

        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)

        if process.returncode:
            try:
                detail = json.loads(stdout or "{}")
            except json.JSONDecodeError:
                detail = {}
            if isinstance(detail, dict) and isinstance(detail.get("error"), dict):
                info = detail["error"]
                raise BackendError(
                    str(info.get("code") or "network_error"),
                    str(info.get("message") or stderr or "HTTP child request failed"),
                    bool(info.get("retryable", True)),
                )
            raise BackendError(
                "network_error",
                (stderr or "HTTP child request failed").strip(),
                retryable=True,
            )
        try:
            decoded = json.loads(stdout)
            return HttpResponse(
                int(decoded["status"]),
                dict(decoded.get("headers") or {}),
                decoded.get("body"),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise BackendError("invalid_transport", "HTTP child returned invalid JSON") from exc

    def cancel(self) -> None:
        """Terminate the current request child, if one exists."""
        process = self._process
        if process is not None and process.poll() is None:
            self._terminate(process)

    def _notify_abort(self, reason: str) -> None:
        if self.on_abort is not None:
            self.on_abort(reason)

    @staticmethod
    def _terminate(process: subprocess.Popen[str]) -> None:
        try:
            process.terminate()
            process.wait(timeout=1)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass


def _child_main() -> int:
    """Execute one serialized request for SubprocessHttpTransport."""
    try:
        specification = json.load(sys.stdin)
        response = _request_with_urllib(
            specification["method"],
            specification["url"],
            headers=specification.get("headers") or {},
            payload=specification.get("payload"),
            timeout=specification.get("timeout"),
        )
        print(
            json.dumps(
                {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": response.body,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except BackendError as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "retryable": exc.retryable,
                    }
                },
                ensure_ascii=False,
            )
        )
        return 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "network_error",
                        "message": str(exc),
                        "retryable": True,
                    }
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    child_args = parser.parse_args()
    raise SystemExit(_child_main() if child_args.child else 2)
