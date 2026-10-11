"""Lifecycle management for a worker-owned Ollama server."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
import subprocess
import time
from typing import Callable
from urllib import request


@dataclass
class OllamaProcessManager:
    """Start, stop and restart only the Ollama process owned by one worker.

    The manager deliberately uses a dedicated local port. An externally
    running Ollama service is never discovered and killed implicitly.
    """

    executable: str = "ollama"
    port: int = 11435
    context_length: int | None = None
    ready_timeout: float = 30
    logger: Callable[..., None] | None = None
    process: subprocess.Popen[str] | None = field(default=None, init=False)

    @property
    def base_url(self) -> str:
        """Return the endpoint assigned to this managed server."""
        return f"http://127.0.0.1:{self.port}"

    @property
    def running(self) -> bool:
        """Report whether the owned server process is still alive."""
        return self.process is not None and self.process.poll() is None

    def start(self) -> None:
        """Start the owned server once and record its process handle."""
        if self.running:
            return
        environment = os.environ.copy()
        environment["OLLAMA_HOST"] = f"127.0.0.1:{self.port}"
        if self.context_length is not None:
            environment["OLLAMA_CONTEXT_LENGTH"] = str(self.context_length)
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.process = subprocess.Popen(
                [self.executable, "serve"],
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                text=True,
            )
        except OSError as exc:
            self.process = None
            raise RuntimeError(
                f"Cannot start worker-owned Ollama process {self.executable!r}: {exc}"
            ) from exc
        try:
            self._wait_ready()
        except Exception:
            self.stop()
            raise
        self._emit("ollama.started", pid=self.process.pid, port=self.port)

    def stop(self) -> None:
        """Terminate the owned Ollama process and its descendants."""
        process = self.process
        self.process = None
        if process is None or process.poll() is not None:
            return
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 and process.poll() is None:
                self._terminate_direct(process)
        else:
            self._terminate_direct(process)
        self._emit("ollama.stopped", pid=process.pid, port=self.port)

    def restart(self) -> None:
        """Replace the owned server after a cancelled or timed-out request."""
        old_pid = self.process.pid if self.process is not None else None
        self.stop()
        self.start()
        new_pid = self.process.pid if self.process is not None else None
        self._emit("ollama.restarted", old_pid=old_pid, pid=new_pid)

    def close(self) -> None:
        """Release the owned server during worker shutdown."""
        self.stop()

    def _emit(self, event: str, **fields: object) -> None:
        if self.logger is not None:
            self.logger(event, **fields)

    def _wait_ready(self) -> None:
        """Wait until this newly started server accepts a tags request."""
        deadline = time.monotonic() + max(float(self.ready_timeout), 0.1)
        endpoint = self.base_url + "/api/tags"
        while time.monotonic() < deadline:
            if self.process is None or self.process.poll() is not None:
                raise RuntimeError("Worker-owned Ollama process exited during startup")
            try:
                with request.urlopen(endpoint, timeout=0.5):
                    return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError(
            f"Worker-owned Ollama did not become ready within {self.ready_timeout:g} seconds"
        )

    @staticmethod
    def _terminate_direct(process: subprocess.Popen[str]) -> None:
        try:
            process.terminate()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
