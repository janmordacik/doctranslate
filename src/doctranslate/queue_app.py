"""File-based queue client and Tk GUI for document translation jobs."""

from __future__ import annotations

import argparse
import copy
import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
import re
import shutil
if os.name != "nt":
    import fcntl
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .ai import StyleLibrary
from .config import CONFIG_FILE, get_language, get_workdir, save_config
from .observability import JsonEventLogger, queue_log_path
from .retention import RetentionPolicy, cleanup_queue_workdirs


ROOT = Path(os.environ.get("TRANSLATE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
DEFAULT_QUEUE = get_workdir() / "queue.json"
WORKER_SCRIPT = Path(__file__).resolve().with_name("queue_worker.py")
WORKER_STATE = ROOT / "worker-state.json"
WORKER_LOCK = ROOT / "worker.lock"
JOB_STATES = ("prepared", "in_progress", "paused", "failed", "done")
LANGUAGE_CHOICES = ("en", "cs", "de", "es", "fr", "it", "pl", "sk")
OLLAMA_URL = os.environ.get("TRANSLATE_OLLAMA_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("TRANSLATE_MODEL", "qwen3.8:27b")

# The catalog is deliberately explicit.  The production worker registers the
# advanced runner lazily per job; provider/model availability is then reported
# as a normal job failure instead of disabling the module in the GUI.
TRANSLATION_MODULES = (
    {"id": "basic", "label": "Basic", "available": True,
     "reason": "linear translation engine"},
    {"id": "advanced", "label": "Advanced", "available": True,
     "reason": "contextual translation with checkpoint and glossary"},
)


def translation_module_catalog() -> tuple[dict[str, object], ...]:
    """Return a defensive catalog used consistently by CLI and GUI."""
    return tuple(dict(item) for item in TRANSLATION_MODULES)


def available_translation_module_ids() -> tuple[str, ...]:
    """Return module IDs that the current composition root can execute."""
    return tuple(item["id"] for item in TRANSLATION_MODULES if item["available"])

GUI_TEXT = {
    "cs": {
        "title": "Translate – fronta úloh", "workdir_group": "Pracovní adresář",
        "general_group": "Obecné", "worker_group": "Worker", "job_group": "Úloha",
        "workdir": "Adresář", "language": "Jazyk", "browse": "Procházet…", "save": "Uložit",
         "start": "Spustit", "send": "Aktualizovat úlohy", "stop": "Zastavit worker", "add": "Přidat", "copy": "Kopírovat",
        "pause": "Pozastavit", "prepare": "Připravit", "delete": "Smazat",
        "up": "Nahoru", "down": "Dolů", "refresh": "Obnovit",
        "order": "Pořadí", "job": "Úloha", "state": "Stav", "input": "Vstup",
        "translator": "Modul",
        "translator_unavailable": "{translator} není dostupný – {reason}",
        "provider": "Poskytovatel", "profile": "Profil", "configure": "Konfigurace…", "login": "Přihlásit",
        "style": "Styl", "style_auto": "automaticky podle autora",
        "source_language": "Zdrojový jazyk", "target_language": "Cílový jazyk",
         "provider_test": "Otestovat spojení", "provider_save": "Uložit", "provider_cancel": "Zrušit", "provider_probe": "Test poskytovatele",
         "login_completed": "Přihlášení dokončeno.",
         "output": "Výstup", "model": "Model", "phase": "Fáze",
        "input_file": "Vstupní PDF", "output_file": "Výstupní PDF",
        "html_file": "Přeložené HTML", "browse_input": "Vybrat PDF…",
        "browse_output": "Vybrat výstup…", "browse_html": "Vybrat HTML…",
        "phase_both": "in -> html -> out", "phase_html": "in -> html",
        "phase_pdf": "html -> out",
        "ok": "OK", "cancel": "Zrušit",
        "input_required": "Vyberte vstupní PDF.",
        "output_required": "Zadejte výstupní PDF.",
        "input_invalid": "Vstup musí být existující PDF soubor.",
        "output_invalid": "Výstup musí být jiné PDF než vstup.",
        "html_invalid": "XHTML/HTML musí mít příponu .html nebo .htm.",
        "same_language": "Při stejném zdrojovém a cílovém jazyce zvolte explicitní styl.",
        "running": "běží", "stopped": "neběží", "unsent": " * neodeslané změny",
         "status": "Worker: {worker} | revize: {revision}{marker}",
         "stopping": "worker se zastavuje…",
        "activity_starting": "spouští se",
        "activity_preparing": "připravuje job",
        "activity_translating": "překládá přes AI",
        "activity_typesetting": "sází PDF z HTML",
        "activity_polling": "kontroluje frontu",
        "unit_pages": "stran", "unit_blocks": "bloků", "unit_items": "položek",
        "models_checking": "ověřuji Ollamu…",
        "models_empty": "Ollama běží, modely nejsou nainstalované",
        "models_offline": "Ollama není dostupná", "models_invalid": "Odpověď Ollamy je neplatná",
        "choose_workdir": "Vyberte pracovní adresář", "invalid_workdir": "Neplatný pracovní adresář",
        "worker_running": "Worker běží", "stop_before_workdir": "Nejprve zastavte worker.",
        "unsent_title": "Neodeslané změny", "discard_workdir": "Změnit adresář a zahodit změny?",
        "discard": "Zahodit neodeslané změny?", "close_unsent": "Zavřít a zahodit neodeslané změny?",
        "choose_pdf": "Vyberte PDF", "pdf_files": "PDF", "all_files": "Všechny soubory",
        "delete_title": "Smazat úlohu", "delete_confirm": "Opravdu smazat vybranou úlohu?",
        "delete_active_title": "Aktivní úloha", "delete_active_confirm": "Úloha právě probíhá. Zastavit worker a po jeho dokončení úlohu smazat?",
        "delete_waiting": "Worker se zastavuje; po dokončení bude aktivní úloha smazána.",
        "preview_title": "Náhled aktuálního bloku",
        "preview_empty": "Náhled se zobrazí při zpracování dávky.",
        "preview_source": "zdroj",
        "preview_translated": "překlad",
        "preview_error": "chyba",
        "preview_truncated": "… náhled zkrácen",
        "prepared": "připraveno", "in_progress": "probíhá", "paused": "pozastaveno",
        "failed": "chyba", "done": "hotovo",
    },
    "en": {
        "title": "Translate – job queue", "workdir_group": "Working directory",
        "general_group": "General", "worker_group": "Worker", "job_group": "Job",
        "workdir": "Directory", "language": "Language", "browse": "Browse…", "save": "Save",
         "start": "Start", "send": "Update jobs", "stop": "Stop worker", "add": "Add", "copy": "Copy",
        "pause": "Pause", "prepare": "Prepare", "delete": "Delete",
        "up": "Up", "down": "Down", "refresh": "Refresh",
        "order": "Order", "job": "Job", "state": "State", "input": "Input",
        "translator": "Module",
        "translator_unavailable": "{translator} unavailable – {reason}",
        "provider": "Provider", "profile": "Profile", "configure": "Configuration…", "login": "Login",
        "style": "Style", "style_auto": "preserve source style",
        "source_language": "Source language", "target_language": "Target language",
         "login_completed": "Login completed.",
         "provider_test": "Test connection", "provider_save": "Save", "provider_cancel": "Cancel", "provider_probe": "Provider probe",
         "output": "Output", "model": "Model", "phase": "Phase",
        "input_file": "Input PDF", "output_file": "Output PDF",
        "html_file": "Translated HTML", "browse_input": "Select PDF…",
        "browse_output": "Select output…", "browse_html": "Select HTML…",
        "phase_both": "in -> html -> out", "phase_html": "in -> html",
        "phase_pdf": "html -> out",
        "ok": "OK", "cancel": "Cancel",
        "input_required": "Select an input PDF.",
        "output_required": "Enter an output PDF.",
        "input_invalid": "The input must be an existing PDF file.",
        "output_invalid": "The output must be a different PDF file.",
        "html_invalid": "XHTML/HTML must use the .html or .htm extension.",
        "same_language": "Choose an explicit style when source and target languages are the same.",
        "running": "running", "stopped": "stopped", "unsent": " * unsent changes",
         "status": "Worker: {worker} | revision: {revision}{marker}",
         "stopping": "worker is stopping…",
        "activity_starting": "starting",
        "activity_preparing": "preparing job",
        "activity_translating": "translating with AI",
        "activity_typesetting": "typesetting PDF from HTML",
        "activity_polling": "checking queue",
        "unit_pages": "pages", "unit_blocks": "blocks", "unit_items": "items",
        "models_checking": "checking Ollama…",
        "models_empty": "Ollama is running, no models installed",
        "models_offline": "Ollama is unavailable", "models_invalid": "Ollama response is invalid",
        "choose_workdir": "Select working directory", "invalid_workdir": "Invalid working directory",
        "worker_running": "Worker is running", "stop_before_workdir": "Stop the worker first.",
        "unsent_title": "Unsent changes", "discard_workdir": "Change directory and discard changes?",
        "discard": "Discard unsent changes?", "close_unsent": "Close and discard unsent changes?",
        "choose_pdf": "Select PDF", "pdf_files": "PDF", "all_files": "All files",
        "delete_title": "Delete job", "delete_confirm": "Delete the selected job?",
        "delete_active_title": "Active job", "delete_active_confirm": "The job is active. Stop the worker and delete the job after it finishes?",
        "delete_waiting": "The worker is stopping; the active job will be deleted when it finishes.",
        "preview_title": "Current block preview",
        "preview_empty": "The preview will appear when a batch is processed.",
        "preview_source": "source",
        "preview_translated": "translation",
        "preview_error": "error",
        "preview_truncated": "… preview truncated",
        "prepared": "prepared", "in_progress": "in progress", "paused": "paused",
        "failed": "failed", "done": "done",
    },
}

def parse_ollama_models(payload: Any) -> tuple[str, ...]:
    """Return sorted local model names from the Ollama /api/tags response."""
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return ()
    names = {
        str(item.get("name")).strip()
        for item in payload["models"]
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }
    return tuple(sorted(names, key=str.casefold))


@dataclass(frozen=True)
class OllamaDiscovery:
    status: str
    models: tuple[str, ...] = ()
    detail: str | None = None


def discover_ollama_models(url: str | None = None, timeout: float = 2.0) -> OllamaDiscovery:
    """Query Ollama without collapsing offline, empty and invalid states."""
    endpoint = (url or OLLAMA_URL).rstrip("/") + "/api/tags"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except json.JSONDecodeError as exc:
        return OllamaDiscovery("invalid", detail=str(exc))
    except (OSError, ValueError, TypeError) as exc:
        return OllamaDiscovery("offline", detail=str(exc))
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return OllamaDiscovery("invalid", detail="expected an object with a models list")
    models = parse_ollama_models(payload)
    return OllamaDiscovery("available" if models else "empty", models=models)


def available_ollama_models(url: str | None = None, timeout: float = 2.0) -> tuple[str, ...]:
    """Compatibility helper returning only names from local Ollama."""
    return discover_ollama_models(url, timeout).models


_HTML_METADATA = re.compile(
    r'<script[^>]+id="doctranslate-metadata"[^>]*>([\s\S]*?)</script>',
    re.IGNORECASE,
)


def _html_metadata(path: Path) -> dict[str, Any] | None:
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
        match = _HTML_METADATA.search(text)
        value = json.loads(match.group(1)) if match else None
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_translation_html(
    infile: str | Path,
    outfile: str | Path,
    *,
    inlang: str = "en",
    outlang: str = "cs",
    explicit: str | Path | None = None,
) -> Path | None:
    """Find a complete translated HTML document for one source PDF.

    Matching uses the source PDF SHA-256 and language metadata, not the
    filename. This also works when a document was moved between machines.
    Explicit paths are returned as-is; automatic discovery accepts only a
    complete matching HTML document.
    """
    source = Path(infile).expanduser().resolve()
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    if not source.is_file():
        return None
    target = Path(outfile).expanduser().resolve()
    try:
        source_hash = _file_sha256(source)
    except OSError:
        return None
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(candidate: Path) -> None:
        candidate = candidate.expanduser().resolve()
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)

    add(target.with_suffix(".html"))
    add(source.with_suffix(".html"))
    for directory in dict.fromkeys((source.parent, target.parent)):
        try:
            for candidate in sorted(directory.glob("*.html")):
                add(candidate)
            for candidate in sorted(directory.glob("*.htm")):
                add(candidate)
        except OSError:
            continue
    for candidate in candidates:
        if not candidate.is_file():
            continue
        metadata = _html_metadata(candidate)
        if (
            metadata
            and metadata.get("complete") is True
            and metadata.get("source_hash") == source_hash
            and metadata.get("inlang") == inlang
            and metadata.get("outlang") == outlang
        ):
            return candidate
    return None


def default_queue_path() -> Path:
    """Return the queue path for the current configured work directory."""
    return get_workdir() / "queue.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str = "job") -> str:
    return prefix + "-" + uuid.uuid4().hex[:12]


def process_status(pid: int | None) -> str:
    """Return alive, dead or unknown without terminating a process."""
    if not isinstance(pid, int) or pid <= 0:
        return "dead"
    if os.name == "nt":
        # os.kill(pid, 0) is not a read-only probe on Windows: it calls
        # TerminateProcess. Query the process handle instead.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return "dead" if ctypes.get_last_error() == 87 else "unknown"
        exit_code = ctypes.c_ulong()
        try:
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return "unknown"
            return "alive" if exit_code.value == 259 else "dead"
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "dead"
    except PermissionError:
        return "unknown"
    except OSError:
        return "dead"
    return "alive"


def process_alive(pid: int | None) -> bool:
    """Conservative boolean wrapper used by status displays."""
    return process_status(pid) == "alive"


class FileLock:
    """Git-style atomic lock file with bounded waiting and stale recovery."""

    def __init__(self, path: Path, timeout: float = 30.0, poll: float = 0.1,
                 stale_after: float = 30.0):
        self.path = Path(path)
        self.timeout = timeout
        self.poll = poll
        self.stale_after = max(5.0, stale_after)
        self._fd: int | None = None
        self._owner_token: str | None = None
        self._mutex_handle = None

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                fd = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                    0o600,
                )
                try:
                    self._lock_fd(fd)
                    self._claim_fd(fd)
                    return
                except BaseException:
                    self._unlock_fd(fd)
                    os.close(fd)
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    raise
            except FileExistsError:
                if self._claim_stale_existing():
                    return
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for lock: {self.path}")
                time.sleep(self.poll)

    def _lock_fd(self, fd: int) -> None:
        if os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            kernel32.WaitForSingleObject.restype = ctypes.c_uint32
            kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            name = r"Local\doctranslate-" + hashlib.sha256(
                str(self.path.resolve()).encode("utf-8")
            ).hexdigest()
            handle = kernel32.CreateMutexW(None, False, name)
            if not handle:
                raise OSError(ctypes.get_last_error(), "CreateMutexW failed")
            result = kernel32.WaitForSingleObject(handle, 0)
            if result not in (0, 0x80):
                kernel32.CloseHandle(handle)
                raise BlockingIOError("lock is held by another process")
            self._mutex_handle = handle
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_fd(self, fd: int) -> None:
        try:
            if os.name == "nt":
                if self._mutex_handle:
                    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                    kernel32.ReleaseMutex(self._mutex_handle)
                    kernel32.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass

    def _claim_fd(self, fd: int) -> None:
        token = uuid.uuid4().hex
        payload = json.dumps({"pid": os.getpid(), "time": utc_now(),
                              "token": token}).encode()
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
        os.fsync(fd)
        self._fd = fd
        self._owner_token = token

    def _claim_stale_existing(self) -> bool:
        try:
            fd = os.open(self.path, os.O_RDWR)
        except FileNotFoundError:
            return False
        claimed = False
        try:
            try:
                self._lock_fd(fd)
            except OSError:
                return False
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                payload = json.loads(
                    os.read(fd, 1 << 20).decode(encoding="utf-8")
                )
                pid = payload.get("pid")
            except (OSError, UnicodeError, ValueError, TypeError):
                try:
                    stale = time.time() - self.path.stat().st_mtime > self.stale_after
                except OSError:
                    stale = False
            else:
                stale = process_status(pid) == "dead"
            if not stale:
                return False
            self._claim_fd(fd)
            claimed = True
            return True
        finally:
            if not claimed:
                self._unlock_fd(fd)
                os.close(fd)

    def _stale(self) -> bool:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            pid = payload.get("pid")
        except (OSError, ValueError, TypeError):
            try:
                return time.time() - self.path.stat().st_mtime > self.stale_after
            except OSError:
                return False
        return process_status(pid) == "dead"

    def release(self) -> None:
        fd, token = self._fd, self._owner_token
        self._fd = None
        self._owner_token = None
        if fd is not None:
            self._unlock_fd(fd)
            os.close(fd)
        if token is None:
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if payload.get("token") == token:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


class StorageError(RuntimeError):
    """A queue/runtime artifact could not be persisted safely."""


def storage_preflight(path: Path, required_bytes: int = 0) -> None:
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    try:
        free = shutil.disk_usage(parent).free
    except OSError as exc:
        raise StorageError(f"Cannot inspect free space for {parent}: {exc}") from exc
    reserve = max(1024 * 1024, required_bytes * 2)
    if free < reserve:
        raise StorageError(
            f"Insufficient free space for {path}: {free} bytes available, "
            f"at least {reserve} bytes recommended"
        )


def atomic_write(path: Path, value: Any) -> None:
    """Write JSON through a temporary file and replace the target atomically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    storage_preflight(path, len(text.encode("utf-8")))
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise StorageError(f"Cannot persist {path}: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


class QueueStore:
    """Persistent queue snapshot; only short locked transactions write it.

    The JSON lock protects the snapshot only. Structured event logging happens
    after the state mutation and never surrounds a translation or Ollama call.
    """

    def __init__(self, path: Path | None = None):
        self.path = Path(path if path is not None else default_queue_path()).expanduser().resolve()
        self.lock = FileLock(self.path.with_suffix(".lock"))
        self.logger = JsonEventLogger(queue_log_path(self.path))

    @staticmethod
    def default() -> dict[str, Any]:
        """Return a queue with one control record and no user jobs."""
        return {
            "schema": 1,
            "revision": 0,
            "updated_at": utc_now(),
            "items": [
                {
                    "kind": "control",
                    "id": "worker-control",
                    "command": None,
                    "request_id": None,
                    "updated_at": None,
                }
            ],
        }

    def _normalise(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or value.get("schema") != 1:
            raise ValueError(f"Invalid queue schema: {self.path}")
        items = value.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Queue items must be a list: {self.path}")
        controls = [item for item in items if isinstance(item, dict) and item.get("kind") == "control"]
        jobs = [item for item in items if isinstance(item, dict) and item.get("kind") == "job"]
        if len(controls) > 1 or len(controls) + len(jobs) != len(items):
            raise ValueError(f"Queue contains unknown or duplicate item kinds: {self.path}")
        control = controls[0] if controls else self.default()["items"][0]
        if control.get("id") != "worker-control" or control.get("command") not in (None, "stop"):
            raise ValueError(f"Invalid worker control item: {self.path}")
        seen_ids: set[str] = set()
        for job in jobs:
            required = ("id", "input", "output", "inlang", "outlang", "phase", "state")
            if any(not isinstance(job.get(key), str) or not job.get(key).strip() for key in required):
                raise ValueError(f"Invalid job fields: {self.path}")
            if job["id"] in seen_ids or job["id"] == "worker-control":
                raise ValueError(f"Duplicate job id: {job['id']}")
            if job["state"] not in JOB_STATES or job["phase"] not in ("both", "html", "pdf"):
                raise ValueError(f"Invalid job state or phase: {job['id']}")
            if job.get("model") is not None and not isinstance(job.get("model"), str):
                raise ValueError(f"Invalid job model: {job['id']}")
            translator_id = job.get("translator_id", "basic")
            if not isinstance(translator_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", translator_id):
                raise ValueError(f"Invalid job translator ID: {job['id']}")
            translator_options = job.get("translator_options", {})
            if not isinstance(translator_options, dict):
                raise ValueError(f"Invalid job translator options: {job['id']}")
            try:
                json.dumps(translator_options)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid job translator options: {job['id']}") from exc
            job["translator_id"] = translator_id
            job["translator_options"] = copy.deepcopy(translator_options)
            if job.get("target_variant") is None:
                job["target_variant"] = "auto"
            if not isinstance(job.get("target_variant"), str) or not job["target_variant"].strip():
                raise ValueError(f"Invalid job target variant: {job['id']}")
            job["target_variant"] = job["target_variant"].strip()
            try:
                from .ai.styles import StyleLibrary

                style_library = StyleLibrary()
                job["target_variant"] = style_library.resolve_variant(
                    job["target_variant"], job["outlang"]
                )
                # Recompute on load so a catalog edit invalidates old cache entries.
                job["style_revision"] = style_library.fingerprint(job["target_variant"])
            except (ImportError, ValueError) as exc:
                raise ValueError(f"Invalid job style profile: {job['id']}") from exc
            if not isinstance(job.get("style_revision"), str) or not job["style_revision"].strip():
                raise ValueError(f"Invalid job style revision: {job['id']}")
            for page_key in ("first_page", "last_page"):
                page_value = job.get(page_key)
                if page_value is not None and (
                    not isinstance(page_value, int) or isinstance(page_value, bool) or page_value < 1
                ):
                    raise ValueError(f"Invalid job {page_key}: {job['id']}")
            if (
                job.get("first_page") is not None
                and job.get("last_page") is not None
                and job["first_page"] > job["last_page"]
            ):
                raise ValueError(f"Invalid job page range: {job['id']}")
            seen_ids.add(job["id"])
        return {
            "schema": 1,
            "revision": int(value.get("revision", 0)),
            "updated_at": value.get("updated_at"),
            "items": [control] + jobs,
        }

    def load(self) -> dict[str, Any]:
        """Read and validate a snapshot, falling back to its backup if needed."""
        if not self.path.exists():
            return self.default()
        try:
            return self._normalise(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            backup = self.path.with_suffix(".bak")
            if backup.exists():
                try:
                    restored = self._normalise(json.loads(backup.read_text(encoding="utf-8")))
                except (OSError, ValueError, json.JSONDecodeError) as backup_exc:
                    raise RuntimeError(
                        f"Cannot read queue {self.path} or its backup {backup}: {backup_exc}"
                    ) from exc
                print(f"WARNING: using valid queue backup {backup}: {exc}", file=sys.stderr)
                return restored
            raise RuntimeError(f"Cannot read queue {self.path}: {exc}") from exc

    def transaction(self, mutator: Callable[[dict[str, Any]], Any]) -> dict[str, Any]:
        """Apply one short revisioned mutation and record its outcome."""
        with self.lock:
            current = self.load()
            before = json.dumps(current, ensure_ascii=False, sort_keys=True)
            result = mutator(copy.deepcopy(current))
            updated = current if result is None else result
            updated = self._normalise(updated)
            updated["revision"] = int(current.get("revision", 0)) + 1
            updated["updated_at"] = utc_now()
            if self.path.exists():
                backup = self.path.with_suffix(".bak")
                try:
                    backup.write_bytes(self.path.read_bytes())
                except OSError as exc:
                    print(f"WARNING: cannot update queue backup {backup}: {exc}", file=sys.stderr)
            if before != json.dumps(updated, ensure_ascii=False, sort_keys=True) or not self.path.exists():
                atomic_write(self.path, updated)
            self.logger.event(
                "queue.transaction",
                revision=updated["revision"],
                changed=before != json.dumps(updated, ensure_ascii=False, sort_keys=True),
            )
            return updated

    def jobs(self) -> list[dict[str, Any]]:
        """Return only jobs, excluding the first worker-control record."""
        return [item for item in self.load()["items"] if item.get("kind") == "job"]

    def set_jobs(self, jobs: list[dict[str, Any]]) -> dict[str, Any]:
        """Replace the ordered job list in one locked revision."""
        def update(data: dict[str, Any]) -> dict[str, Any]:
            control = data["items"][0]
            data["items"] = [control] + jobs
            return data
        return self.transaction(update)

    def append_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Append a job inside the same locked transaction as the read."""
        def update(data: dict[str, Any]) -> dict[str, Any]:
            data["items"].append(copy.deepcopy(job))
            return data
        return self.transaction(update)

    def merge_jobs(self, jobs: list[dict[str, Any]], base_jobs: list[dict[str, Any]],
                   base_revision: int, *, allow_active_delete: bool = False) -> dict[str, Any]:
        """Publish a GUI draft while preserving concurrent worker fields."""
        return self.transaction(
            lambda data: merge_queue_jobs(
                data, jobs, base_jobs, base_revision,
                allow_active_delete=allow_active_delete,
            )
        )

    def update_job(self, job_id: str, **changes: Any) -> dict[str, Any]:
        """Apply a small state or runtime update to one job atomically."""
        def update(data: dict[str, Any]) -> dict[str, Any]:
            for item in data["items"]:
                if item.get("kind") == "job" and item.get("id") == job_id:
                    item.update(changes)
                    item["updated_at"] = utc_now()
                    return data
            raise KeyError(f"Unknown job: {job_id}")
        return self.transaction(update)

    def request_stop(self) -> dict[str, Any]:
        """Publish the cooperative worker-stop command in the queue control row."""
        def update(data: dict[str, Any]) -> dict[str, Any]:
            control = data["items"][0]
            control.update(command="stop", request_id=new_id("stop"), updated_at=utc_now())
            return data
        return self.transaction(update)

    def consume_stop(self) -> dict[str, Any]:
        """Clear a stop command after the worker has observed it."""
        def update(data: dict[str, Any]) -> dict[str, Any]:
            data["items"][0].update(command=None, request_id=None, updated_at=utc_now())
            return data
        return self.transaction(update)

    def cancel_stop(self) -> bool:
        """Clear a pending stop so Start/Update can resume a live worker."""
        cleared = False

        def update(data: dict[str, Any]) -> dict[str, Any]:
            nonlocal cleared
            control = data["items"][0]
            if control.get("command") == "stop":
                control.update(command=None, request_id=None, updated_at=utc_now())
                cleared = True
            return data
        self.transaction(update)
        return cleared


class QueueConflictError(RuntimeError):
    """Raised when a GUI draft conflicts with a newer worker update."""


def merge_queue_jobs(current_data: dict[str, Any], jobs: list[dict[str, Any]],
                     base_jobs: list[dict[str, Any]], base_revision: int,
                     *, allow_active_delete: bool = False) -> dict[str, Any]:
    """Merge user edits while preserving worker fields.

    An ``in_progress`` job may be removed only after the caller has verified
    that no worker is live. The default guard protects against a stale GUI or
    another client deleting a job while its worker can still write progress.
    """
    runtime_fields = {"state", "progress", "error", "started_at", "completed_at", "traceback"}
    base_by_id = {job["id"]: job for job in base_jobs}
    draft_by_id = {job["id"]: job for job in jobs}
    current_jobs = [item for item in current_data["items"] if item.get("kind") == "job"]
    current_by_id = {job["id"]: job for job in current_jobs}
    merged: list[dict[str, Any]] = []
    for draft in jobs:
        current = current_by_id.get(draft["id"])
        base = base_by_id.get(draft["id"])
        item = copy.deepcopy(draft)
        if current is not None and base is not None and current_data.get("revision") != base_revision:
            if (draft.get("state") != base.get("state")
                    and current.get("state") != base.get("state")
                    and current.get("state") != draft.get("state")):
                raise QueueConflictError(f"Job state changed concurrently: {draft['id']}")
            for field in runtime_fields:
                if draft.get(field) == base.get(field):
                    if field in current:
                        item[field] = current[field]
                    else:
                        item.pop(field, None)
        merged.append(item)
    for current in current_jobs:
        if current["id"] not in draft_by_id and current["id"] not in base_by_id:
            merged.append(copy.deepcopy(current))
        elif (current["id"] not in draft_by_id
              and current.get("state") == "in_progress"
              and not allow_active_delete):
            raise QueueConflictError(f"Cannot delete active job: {current['id']}")
    current_data["items"] = [current_data["items"][0]] + merged
    return current_data

def make_job(
    infile: str | Path,
    outfile: str | Path | None = None,
    *,
    inlang: str = "en",
    outlang: str = "cs",
    model: str | None = None,
    provider: str = "ollama",
    profile: str | None = None,
    input_format: str | None = None,
    output_format: str | None = None,
    phase: str = "both",
    target_variant: str = "auto",
    style_revision: str | None = None,
    translator_id: str = "basic",
    translator_options: Mapping[str, Any] | None = None,
    html_file: str | Path | None = None,
    first_page: int | None = None,
    last_page: int | None = None,
) -> dict[str, Any]:
    """Create a validated queue record; persistence is performed by QueueStore."""
    source = Path(infile).expanduser().resolve()
    target = Path(outfile).expanduser().resolve() if outfile else source.with_name(
        f"{source.stem}-{outlang}-layout.pdf"
    )
    return {
        "kind": "job",
        "id": new_id(),
        "input": str(source),
        "output": str(target),
        "inlang": inlang,
        "outlang": outlang,
        "model": model,
        "provider": provider,
        "profile": profile,
        "input_format": input_format,
        "output_format": output_format,
        "phase": phase,
        "target_variant": target_variant or "auto",
        "style_revision": style_revision,
        "translator_id": translator_id or "basic",
        "translator_options": copy.deepcopy(translator_options or {}),
        **({"html_file": str(Path(html_file).expanduser().resolve())} if html_file else {}),
        **({"first_page": first_page} if first_page is not None else {}),
        **({"last_page": last_page} if last_page is not None else {}),
        "state": "prepared",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "error": None,
    }


class WorkerController:
    """Start and control the worker without a persistent IPC server.

    Stop is intentionally cooperative: the command is observed after the
    current translation batch. The GUI therefore derives its stopping state
    from both the command and worker liveness.
    """

    def __init__(self, queue_path: Path | None = None):
        self.queue = QueueStore(queue_path)
        self.state_path = self.queue.path.with_name("worker-state.json")
        self.worker_lock = self.queue.path.with_name("worker.lock")
        self.logger = self.queue.logger

    def running(self) -> bool:
        """Return liveness, allowing a long Ollama request beyond heartbeat."""
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return False
        pid_status = process_status(state.get("pid"))
        if pid_status != "alive":
            return False
        heartbeat = state.get("heartbeat")
        try:
            fresh = time.time() - datetime.fromisoformat(heartbeat).timestamp() < 15
        except (TypeError, ValueError):
            fresh = False
        # A long Ollama request may exceed the heartbeat interval. The worker
        # lock proves that this process still owns the active worker slot.
        return fresh or self.worker_lock.exists()

    def state_snapshot(self) -> dict[str, Any]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def stopping(self) -> bool:
        """Return true only while a live worker still owns a pending stop."""
        if not self.running():
            return False
        try:
            return self.queue.load()["items"][0].get("command") == "stop"
        except (OSError, ValueError, RuntimeError, KeyError, IndexError):
            return False

    def start(self) -> bool:
        """Cancel a pending stop, then start only if no worker is live."""
        self.cancel_stop()
        if self.running():
            self.logger.event("worker.start.skipped", reason="already_running")
            return False
        command = [sys.executable, "-m", "doctranslate.queue_worker", "--queue", str(self.queue.path)]
        log_path = self.queue.path.with_name("worker.log")
        environment = os.environ.copy()
        source_path = str(Path(__file__).resolve().parents[2])
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (source_path, environment.get("PYTHONPATH", "")) if part
        )
        kwargs: dict[str, Any] = {
            "cwd": str(ROOT),
            "stdin": subprocess.DEVNULL,
            "env": environment,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
                subprocess, "DETACHED_PROCESS", 0
            )
        try:
            with log_path.open("ab") as log:
                subprocess.Popen(command, stdout=log, stderr=log, **kwargs)
        except OSError as exc:
            self.logger.event("worker.start.failed", error_type=type(exc).__name__, error=str(exc))
            raise RuntimeError(f"Cannot start worker; see {log_path}: {exc}") from exc
        self.logger.event("worker.start.requested", queue=str(self.queue.path))
        return True

    def stop(self) -> None:
        # Do not leave a one-shot stop request behind when no worker exists.
        if self.running():
            self.queue.request_stop()
            self.logger.event("worker.stop.requested", queue=str(self.queue.path))
        else:
            self.logger.event("worker.stop.skipped", reason="already_stopped")

    def cancel_stop(self) -> bool:
        """Cancel a pending stop and report whether a command was present."""
        pending = self.queue.cancel_stop()
        if pending:
            self.logger.event("worker.stop.cancelled", queue=str(self.queue.path))
        return pending


def update_queue_and_start(
    store: QueueStore,
    jobs: list[dict[str, Any]],
    *,
    start_worker: bool = True,
) -> bool:
    """Publish a complete job list and optionally start the singleton worker."""
    store.set_jobs(jobs)
    controller = WorkerController(store.path)
    return controller.start() if start_worker else False


def format_status(store: QueueStore) -> str:
    jobs = store.jobs()
    controller = WorkerController(store.path)
    state = controller.state_snapshot()
    detail = state.get("activity") or state.get("state")
    progress = state.get("progress")
    completed = state.get("completed")
    total = state.get("total")
    progress_text = ""
    if isinstance(progress, (int, float)) and isinstance(completed, (int, float)) and isinstance(total, (int, float)) and total > 0:
        progress_text = f" progress={round(float(progress) * 100)}% ({int(completed)}/{int(total)} {state.get('unit', 'items')})"
    lines = [f"worker={'running' if controller.running() else 'stopped'}"
             + (f" activity={detail}" if detail else "") + progress_text]
    if not jobs:
        lines.append("(empty queue)")
    for index, job in enumerate(jobs, 1):
        lines.append(
            f"{index:>3} {job['id']:<18} {job.get('state', 'prepared'):<12} "
            f"{Path(job.get('input', '')).name}"
        )
    return "\n".join(lines)


def cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="translate.cmd")
    parser.add_argument("--queue", type=Path, default=None, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a job and start the worker")
    add.add_argument("infile", type=Path)
    add.add_argument("--outfile", type=Path)
    add.add_argument("--inlang", default="en")
    add.add_argument("--outlang", default="cs")
    add.add_argument("--model")
    add.add_argument("--translator", default="basic", metavar="ID",
                     help="translation module ID; default: basic")
    add.add_argument("--provider", default="ollama")
    add.add_argument("--profile")
    add.add_argument("--input-format")
    add.add_argument("--output-format")
    add.add_argument("--phase", choices=("both", "html", "pdf"), default="both")
    add.add_argument("--htmlfile", type=Path, help="translated HTML for the pdf phase")

    start = sub.add_parser("start", help="start or resume the worker")
    start.set_defaults()

    pause = sub.add_parser("pause", help="pause a selected job after the current batch")
    pause.add_argument("job_id")

    stop = sub.add_parser("stop", help="stop the worker after the current batch")

    status = sub.add_parser("status", help="show queue and worker status")
    status.add_argument("--json", action="store_true")

    cleanup = sub.add_parser("cleanup", help="remove aged reproducible run artifacts")
    cleanup.add_argument("--dry-run", action="store_true", help="list candidates without removing them")
    cleanup.add_argument("--older-than-days", type=int, default=30, metavar="N")

    args = parser.parse_args(argv)
    store = QueueStore(args.queue)
    store.logger.event("cli.command", command=args.command)

    if args.command == "add":
        if not args.infile.is_file():
            parser.error(f"Input file does not exist: {args.infile}")
        store.append_job(make_job(
            args.infile, args.outfile, inlang=args.inlang, outlang=args.outlang,
            model=args.model, translator_id=args.translator,
            provider=args.provider, profile=args.profile,
            input_format=args.input_format, output_format=args.output_format,
            phase=args.phase, html_file=args.htmlfile,
        ))
        WorkerController(store.path).start()
        print(format_status(store))
        return 0
    if args.command == "start":
        started = WorkerController(store.path).start()
        print("worker started" if started else "worker already running")
        return 0
    if args.command == "pause":
        store.update_job(args.job_id, state="paused", error=None)
        print(format_status(store))
        return 0
    if args.command == "stop":
        controller = WorkerController(store.path)
        if controller.running():
            store.request_stop()
            print("stop requested")
        else:
            print("worker already stopped")
        return 0
    if args.command == "status":
        if args.json:
            print(json.dumps(store.load(), ensure_ascii=False, indent=2))
        else:
            print(format_status(store))
        return 0
    if args.command == "cleanup":
        try:
            reports = cleanup_queue_workdirs(
                store.path,
                policy=RetentionPolicy(sidecar_days=args.older_than_days),
                dry_run=args.dry_run,
            )
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))
        return 0
    return 2


class QueueGui:
    """Tk queue editor with grouped controls and cs/en localization."""

    def __init__(self, queue_path: Path | None = None):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.messagebox = messagebox
        self.language = get_language()
        self.queue_path = (
            Path(queue_path).expanduser().resolve()
            if queue_path is not None
            else default_queue_path()
        )
        self.workdir = self.queue_path.parent
        self.store = QueueStore(self.queue_path)
        self.controller = WorkerController(self.queue_path)
        self.root = tk.Tk()
        self.root.geometry("1120x760")
        self.dirty = False
        self.form_editing = False
        self.auto_output_suggestion: str | None = None
        self.auto_html_suggestion: str | None = None
        self.editing_job_template: dict[str, Any] | None = None
        snapshot = self.store.load()
        self.base_revision = snapshot.get("revision", 0)
        self.base_jobs = copy.deepcopy(self.store.jobs())
        self.jobs_draft = copy.deepcopy(self.base_jobs)
        self.status = tk.StringVar(value="")
        self.workdir_var = tk.StringVar(value=str(self.workdir))
        self.language_var = tk.StringVar(value=self.language)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.provider_var = tk.StringVar(value="ollama")
        self.translator_var = tk.StringVar(value="basic")
        self.translation_module_choices = available_translation_module_ids()
        self.profile_var = tk.StringVar(value="")
        self.style_var = tk.StringVar(value="auto")
        self.style_display_var = tk.StringVar(value="")
        self.source_language_var = tk.StringVar(value="en")
        self.target_language_var = tk.StringVar(value="cs")
        self.phase_var = tk.StringVar(value="both")
        self.phase_display_var = tk.StringVar(value="")
        self.input_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value="")
        self.html_file_var = tk.StringVar(value="")
        self.phase_choices = ("both", "html", "pdf")
        self.phase_display_choices = ()
        self.provider_choices = ("ollama", "openai", "gemini", "claude")
        self.profile_choices = ()
        self.style_library = StyleLibrary()
        self.style_choices = self._style_choices_for_language("cs")
        self.style_display_choices = ()
        self.model_choices = [DEFAULT_MODEL]
        self.model_discovery = OllamaDiscovery("offline")
        self.model_refreshing = False
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.frames: dict[str, Any] = {}
        self.labels: dict[str, Any] = {}
        self.buttons: dict[str, Any] = {}

        workdir_group = tk.LabelFrame(self.root)
        workdir_group.pack(fill="x", padx=8, pady=(8, 0))
        self.frames["workdir"] = workdir_group
        tk.Entry(workdir_group, textvariable=self.workdir_var).pack(
            side="left", fill="x", expand=True, padx=6, pady=4
        )
        self.buttons["browse"] = tk.Button(workdir_group, command=self.choose_workdir)
        self.buttons["browse"].pack(side="left", padx=2)
        self.buttons["save_workdir"] = tk.Button(workdir_group, command=self.apply_workdir)
        self.buttons["save_workdir"].pack(side="left", padx=(2, 6))

        general_group = tk.LabelFrame(self.root)
        general_group.pack(fill="x", padx=8, pady=(6, 0))
        self.frames["general"] = general_group
        self.labels["language"] = tk.Label(general_group)
        self.labels["language"].pack(side="left", padx=(6, 2))
        self.language_combo = ttk.Combobox(
            general_group, textvariable=self.language_var, values=("cs", "en"),
            state="readonly", width=7
        )
        self.language_combo.pack(side="left", padx=(2, 8), pady=4)
        self.language_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.buttons["refresh"] = tk.Button(general_group, command=self.refresh)
        self.buttons["refresh"].pack(side="left", padx=8, pady=4)

        worker_group = tk.LabelFrame(self.root)
        worker_group.pack(fill="x", padx=8, pady=(6, 0))
        self.frames["worker"] = worker_group
        for key, command in (("start", self.start), ("send", self.send), ("stop", self.stop)):
            self.buttons[key] = tk.Button(worker_group, command=command)
            self.buttons[key].pack(side="left", padx=2, pady=4)

        job_group = tk.LabelFrame(self.root)
        job_group.pack(fill="x", padx=8, pady=(6, 0))
        self.frames["job"] = job_group
        job_controls = tk.Frame(job_group)
        job_controls.pack(fill="x")
        self.labels["translator"] = tk.Label(job_controls)
        self.labels["translator"].pack(side="left", padx=(6, 2), pady=4)
        self.translator_combo = ttk.Combobox(
            job_controls, textvariable=self.translator_var,
            values=self.translation_module_choices, state="readonly", width=11
        )
        self.translator_combo.pack(side="left", padx=(2, 4), pady=4)
        self.translator_combo.bind("<<ComboboxSelected>>", self.change_translator)
        self.labels["translator_status"] = tk.Label(job_controls, anchor="w")
        self.labels["translator_status"].pack(side="left", padx=(0, 6), pady=4)
        self.labels["provider"] = tk.Label(job_controls)
        self.labels["provider"].pack(side="left", padx=(6, 2), pady=4)
        self.provider_combo = ttk.Combobox(
            job_controls, textvariable=self.provider_var, values=self.provider_choices,
            state="readonly", width=12
        )
        self.provider_combo.pack(side="left", padx=(2, 6), pady=4)
        self.provider_combo.bind("<<ComboboxSelected>>", self.change_provider)
        self.labels["profile"] = tk.Label(job_controls)
        self.labels["profile"].pack(side="left", padx=(2, 2), pady=4)
        self.profile_combo = ttk.Combobox(
            job_controls, textvariable=self.profile_var, values=self.profile_choices,
            state="readonly", width=14
        )
        self.profile_combo.pack(side="left", padx=(2, 6), pady=4)
        self.profile_combo.bind("<<ComboboxSelected>>", self.change_profile)
        self.buttons["configure"] = tk.Button(job_controls, command=self.configure_provider)
        self.buttons["configure"].pack(side="left", padx=2, pady=4)
        self.buttons["login"] = tk.Button(job_controls, command=self.login_provider)
        self.buttons["login"].pack(side="left", padx=2, pady=4)
        self.labels["job_model"] = tk.Label(job_controls)
        self.labels["job_model"].pack(side="left", padx=(6, 2), pady=4)
        self.model_combo = ttk.Combobox(
            job_controls, textvariable=self.model_var, values=tuple(self.model_choices),
            state="readonly", width=24
        )
        self.model_combo.pack(side="left", padx=(2, 10), pady=4)
        self.model_combo.bind("<<ComboboxSelected>>", self.change_model)
        self.labels["model_status"] = tk.Label(job_controls, anchor="w")
        self.labels["model_status"].pack(side="left", padx=(0, 6), pady=4)
        for key, command in (
            ("add", self.add), ("copy", self.copy_selected_job), ("pause", self.pause), ("prepare", self.prepare),
            ("delete", self.delete), ("up", lambda: self.move(-1)),
            ("down", lambda: self.move(1)),
        ):
            self.buttons[key] = tk.Button(job_controls, command=command)
            self.buttons[key].pack(side="left", padx=2, pady=4)

        job_detail = tk.Frame(job_group)
        job_detail.pack(fill="x", padx=2, pady=(0, 4))
        input_row = tk.Frame(job_detail)
        input_row.pack(fill="x")
        self.labels["input_file"] = tk.Label(input_row, width=15, anchor="w")
        self.labels["input_file"].pack(side="left", padx=(6, 2), pady=3)
        self.input_file_entry = tk.Entry(input_row, textvariable=self.input_var, state="readonly")
        self.input_file_entry.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=3)
        self.buttons["browse_input"] = tk.Button(input_row, command=self.choose_input)
        self.buttons["browse_input"].pack(side="left", padx=(2, 6), pady=3)

        output_row = tk.Frame(job_detail)
        output_row.pack(fill="x")
        self.labels["output_file"] = tk.Label(output_row, width=15, anchor="w")
        self.labels["output_file"].pack(side="left", padx=(6, 2), pady=3)
        self.output_file_entry = tk.Entry(output_row, textvariable=self.output_var, state="readonly")
        self.output_file_entry.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=3)
        self.buttons["browse_output"] = tk.Button(output_row, command=self.choose_output)
        self.buttons["browse_output"].pack(side="left", padx=(2, 6), pady=3)

        language_row = tk.Frame(job_detail)
        language_row.pack(fill="x")
        self.labels["source_language"] = tk.Label(language_row)
        self.labels["source_language"].pack(side="left", padx=(6, 2), pady=3)
        self.source_language_combo = ttk.Combobox(
            language_row, textvariable=self.source_language_var, values=LANGUAGE_CHOICES,
            state="readonly", width=8
        )
        self.source_language_combo.pack(side="left", padx=(2, 10), pady=3)
        self.labels["target_language"] = tk.Label(language_row)
        self.labels["target_language"].pack(side="left", padx=(6, 2), pady=3)
        self.target_language_combo = ttk.Combobox(
            language_row, textvariable=self.target_language_var, values=LANGUAGE_CHOICES,
            state="readonly", width=8
        )
        self.target_language_combo.pack(side="left", padx=(2, 10), pady=3)
        self.target_language_combo.bind("<<ComboboxSelected>>", self.change_target_language)

        options_row = tk.Frame(job_detail)
        options_row.pack(fill="x")
        self.labels["phase"] = tk.Label(options_row)
        self.labels["phase"].pack(side="left", padx=(6, 2), pady=3)
        self.phase_combo = ttk.Combobox(
            options_row, textvariable=self.phase_display_var, values=self.phase_display_choices,
            state="readonly", width=20,
        )
        self.phase_combo.pack(side="left", padx=(2, 10), pady=3)
        self.phase_combo.bind("<<ComboboxSelected>>", self.change_phase)
        self.labels["style"] = tk.Label(options_row)
        self.labels["style"].pack(side="left", padx=(6, 2), pady=3)
        self.style_combo = ttk.Combobox(
            options_row,
            textvariable=self.style_display_var,
            values=self.style_display_choices,
            state="readonly",
            width=30,
        )
        self.style_combo.pack(side="left", padx=(2, 6), pady=3)
        self.style_combo.bind("<<ComboboxSelected>>", self.change_style)
        self.labels["html_file"] = tk.Label(options_row)
        self.labels["html_file"].pack(side="left", padx=(2, 2), pady=3)
        self.html_file_entry = tk.Entry(options_row, textvariable=self.html_file_var, state="readonly")
        self.html_file_entry.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=3)
        self.buttons["browse_html"] = tk.Button(options_row, command=self.choose_html)
        self.buttons["browse_html"].pack(side="left", padx=(2, 6), pady=3)

        form_actions = tk.Frame(job_detail)
        form_actions.pack(fill="x")
        self.buttons["ok"] = tk.Button(form_actions, command=self.commit_job_form)
        self.buttons["ok"].pack(side="left", padx=(6, 2), pady=3)
        self.buttons["cancel"] = tk.Button(form_actions, command=self.cancel_job_form)
        self.buttons["cancel"].pack(side="left", padx=2, pady=3)

        columns = ("order", "id", "state", "input", "output", "model")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.column_keys = {
            "order": "order", "id": "job", "state": "state",
            "input": "input", "output": "output", "model": "model",
        }
        widths = {"order": 35, "id": 135, "state": 105, "input": 280, "output": 280, "model": 160}
        for column in columns:
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self.tree.bind("<<TreeviewSelect>>", self.select_job)
        preview_frame = tk.LabelFrame(self.root, text=self._t("preview_title"))
        preview_frame.pack(fill="x", padx=8, pady=(0, 4))
        preview_body = tk.Frame(preview_frame)
        preview_body.pack(fill="x", padx=4, pady=4)
        self.preview_text = tk.Text(
            preview_body,
            height=10,
            wrap="word",
            state="disabled",
            takefocus=False,
        )
        self.preview_scroll = tk.Scrollbar(
            preview_body,
            orient="vertical",
            command=self.preview_text.yview,
        )
        self.preview_text.configure(yscrollcommand=self.preview_scroll.set)
        self.preview_text.pack(side="left", fill="both", expand=True)
        self.preview_scroll.pack(side="right", fill="y")
        status_bar = tk.Frame(self.root, relief="sunken", borderwidth=1)
        status_bar.pack(fill="x", padx=8, pady=(0, 8))
        self.progress = ttk.Progressbar(status_bar, orient="horizontal", mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=6, pady=(4, 0))
        self.labels["status"] = tk.Label(status_bar, anchor="w")
        self.labels["status"].pack(fill="x", padx=6, pady=3)
        self.refresh_labels()
        self.render()
        self.poll()
        self.refresh_models()

    def _t(self, key: str) -> str:
        return GUI_TEXT.get(self.language, GUI_TEXT["en"]).get(key, key)

    def _translation_module_status_text(self) -> str:
        unavailable = [item for item in translation_module_catalog() if not item["available"]]
        if not unavailable:
            return ""
        item = unavailable[0]
        return self._t("translator_unavailable").format(
            translator=item["label"], reason=item["reason"]
        )

    def _refresh_translation_controls(self) -> None:
        self.translation_module_choices = available_translation_module_ids()
        self.translator_combo.configure(values=self.translation_module_choices)
        if self.translator_var.get().strip() not in self.translation_module_choices:
            # Existing advanced jobs remain inspectable, but cannot be newly
            # selected or silently downgraded while editing.
            self.translator_var.set(self.translator_var.get().strip() or "basic")
        self.labels["translator_status"].configure(text=self._translation_module_status_text())

    def _provider_options(self) -> dict[str, object]:
        from .gui.provider_dialogs import provider_options

        return provider_options(self.provider_var.get().strip() or "ollama")

    def _refresh_provider_controls(self) -> None:
        """Show only provider settings supported by the selected provider."""
        options = self._provider_options()
        controls = (
            ("provider_label", self.labels["provider"], True, {"side": "left", "padx": (6, 2), "pady": 4}),
            ("provider_combo", self.provider_combo, True, {"side": "left", "padx": (2, 6), "pady": 4}),
            ("profile_label", self.labels["profile"], bool(options["has_profile"]),
             {"side": "left", "padx": (2, 2), "pady": 4}),
            ("profile_combo", self.profile_combo, bool(options["has_profile"]),
             {"side": "left", "padx": (2, 6), "pady": 4}),
            ("configure", self.buttons["configure"], bool(options["has_configuration"]),
             {"side": "left", "padx": 2, "pady": 4}),
            ("login", self.buttons["login"], bool(options["supports_login"]),
             {"side": "left", "padx": 2, "pady": 4}),
        )
        for _key, widget, _visible, _pack in controls:
            widget.pack_forget()
        # Pack backwards before the common model controls to preserve order.
        for _key, widget, visible, pack in reversed(controls):
            if visible:
                widget.pack(before=self.labels["job_model"], **pack)
        self.profile_choices = self._profiles_for_provider()
        self.profile_combo.configure(values=self.profile_choices)
        if self.profile_var.get() not in self.profile_choices:
            self.profile_var.set("")
        self.labels["model_status"].configure(text=self._model_status_text())

    def _set_job_form_state(self, editing: bool) -> None:
        """Switch the Job detail between readonly view and local draft editing."""
        self.form_editing = editing
        entry_state = "normal" if editing else "readonly"
        combo_state = "readonly" if editing else "disabled"
        model_state = "readonly" if not editing or self._provider_options()["model_discovery"] else "normal"
        for widget in (self.input_file_entry, self.output_file_entry, self.html_file_entry):
            widget.configure(state=entry_state)
        for widget in (self.translator_combo, self.provider_combo, self.profile_combo, self.phase_combo, self.style_combo):
            widget.configure(state=combo_state)
        for widget in (self.source_language_combo, self.target_language_combo):
            widget.configure(state=combo_state)
        self.model_combo.configure(state=model_state)
        for key in ("browse_input", "browse_output", "browse_html", "configure", "login"):
            self.buttons[key].configure(state="normal" if editing else "disabled")
        for key in ("copy", "pause", "prepare", "delete", "up", "down"):
            self.buttons[key].configure(state="disabled" if editing else "normal")
        for key in ("start", "send"):
            self.buttons[key].configure(state="disabled" if editing else "normal")
        self.buttons["add"].configure(state="disabled" if editing else "normal")
        if editing:
            self.buttons["ok"].pack(side="left", padx=(6, 2), pady=3)
            self.buttons["cancel"].pack(side="left", padx=2, pady=3)
        else:
            self.buttons["ok"].pack_forget()
            self.buttons["cancel"].pack_forget()
        if hasattr(self, "tree"):
            try:
                self.tree.state(["disabled"] if editing else ["!disabled"])
            except Exception:
                pass

    def _has_unsent_changes(self) -> bool:
        return self.dirty or self.form_editing

    def _profiles_for_provider(self) -> tuple[str, ...]:
        if not self._provider_options()["has_profile"]:
            return ()
        try:
            from .ai import ProfileStore

            profiles = ProfileStore(CONFIG_FILE).list()
        except Exception:
            return ()
        provider = self.provider_var.get().strip() or "ollama"
        return tuple(item.profile_id for item in profiles if item.provider_id == provider)

    def _log_action(self, action: str, **fields: Any) -> None:
        """Record user actions without logging every polling refresh."""
        self.store.logger.event("gui.action", action=action, **fields)

    def refresh_labels(self) -> None:
        self.root.title(self._t("title"))
        self.frames["workdir"].configure(text=self._t("workdir_group"))
        self.frames["general"].configure(text=self._t("general_group"))
        self.frames["worker"].configure(text=self._t("worker_group"))
        self.frames["job"].configure(text=self._t("job_group"))
        self.labels["language"].configure(text=self._t("language"))
        self.buttons["browse"].configure(text=self._t("browse"))
        self.buttons["save_workdir"].configure(text=self._t("save"))
        self.labels["job_model"].configure(text=self._t("model"))
        self.labels["translator"].configure(text=self._t("translator"))
        self.labels["translator_status"].configure(text=self._translation_module_status_text())
        self.labels["model_status"].configure(text=self._model_status_text())
        for key in ("start", "send", "stop", "add", "copy", "pause", "prepare", "delete", "up", "down", "refresh", "configure", "login"):
            self.buttons[key].configure(text=self._t(key))
        self.labels["provider"].configure(text=self._t("provider"))
        self.labels["profile"].configure(text=self._t("profile"))
        self.labels["input_file"].configure(text=self._t("input_file"))
        self.labels["output_file"].configure(text=self._t("output_file"))
        self.labels["phase"].configure(text=self._t("phase"))
        self.labels["style"].configure(text=self._t("style"))
        self.labels["source_language"].configure(text=self._t("source_language"))
        self.labels["target_language"].configure(text=self._t("target_language"))
        self.labels["html_file"].configure(text=self._t("html_file"))
        self.buttons["browse_input"].configure(text=self._t("browse_input"))
        self.buttons["browse_output"].configure(text=self._t("browse_output"))
        self.buttons["browse_html"].configure(text=self._t("browse_html"))
        self.buttons["ok"].configure(text=self._t("ok"))
        self.buttons["cancel"].configure(text=self._t("cancel"))
        self.phase_display_choices = tuple(
            self._phase_display(phase) for phase in self.phase_choices
        )
        self.phase_combo.configure(values=self.phase_display_choices)
        self._set_phase_value(self.phase_var.get())
        self.style_display_choices = tuple(
            self._style_display(style_id) for style_id in self.style_choices
        )
        self.style_combo.configure(values=self.style_display_choices)
        self._set_style_value(self.style_var.get())
        self._refresh_translation_controls()
        self._refresh_provider_controls()
        self._set_job_form_state(self.form_editing)
        for column, key in self.column_keys.items():
            self.tree.heading(column, text=self._t(key))

    def _model_status_text(self) -> str:
        if not self._provider_options()["model_discovery"]:
            return ""
        discovery = self.model_discovery
        if discovery.status == "available":
            return ""
        return self._t(f"models_{discovery.status}")

    def _worker_activity_text(self, state: dict[str, Any]) -> str:
        activity = str(state.get("activity") or state.get("state") or "").strip()
        if not activity:
            return ""
        label = self._t(f"activity_{activity}")
        if label == f"activity_{activity}":
            label = activity
        phase = self._phase_display(state.get("phase"))
        detail = f"{label} [{phase}]" if phase else label
        completed = state.get("completed")
        total = state.get("total")
        if isinstance(completed, (int, float)) and isinstance(total, (int, float)) and total > 0:
            progress = state.get("progress")
            if not isinstance(progress, (int, float)):
                progress = completed / total
            percent = max(0, min(100, round(float(progress) * 100)))
            unit_key = f"unit_{state.get('unit', 'items')}"
            unit = self._t(unit_key)
            if unit == unit_key:
                unit = str(state.get("unit") or "items")
            detail = f"{detail} – {int(completed)}/{int(total)} {unit} ({percent} %)"
        return detail

    def _render_preview(self, state: dict[str, Any]) -> None:
        """Render only the latest worker snapshot; never modify the queue."""
        widget = getattr(self, "preview_text", None)
        if widget is None:
            return
        preview = state.get("preview")
        if not isinstance(preview, dict):
            content = self._t("preview_empty")
        else:
            stage = str(preview.get("stage") or "source")
            stage_label = self._t({
                "source": "preview_source",
                "translating": "preview_source",
                "translated": "preview_translated",
                "error": "preview_error",
            }.get(stage, "preview_source"))
            block_id = str(preview.get("block_id") or "")
            page = preview.get("page")
            location = f"{block_id}"
            if isinstance(page, int):
                location = f"p. {page}, {location}"
            text = preview.get("translated_text") if stage == "translated" else preview.get("source_text")
            text = str(text or self._t("preview_empty"))
            content = f"{location} | {stage_label}\n{text}"
            if preview.get("truncated"):
                content += f"\n{self._t('preview_truncated')}"
            if stage == "error" and preview.get("error"):
                content += f"\n{self._t('preview_error')}: {preview['error']}"
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _phase_display(self, phase: Any) -> str:
        """Return a format-neutral phase label for the GUI."""
        value = str(phase or "").strip()
        if value in self.phase_choices:
            return self._t(f"phase_{value}")
        return value

    def _set_phase_value(self, phase: Any) -> None:
        value = str(phase or "both").strip()
        if value not in self.phase_choices:
            value = "both"
        self.phase_var.set(value)
        self.phase_display_var.set(self._phase_display(value))

    def _style_display(self, style_id: str) -> str:
        if style_id == "auto":
            return self._t("style_auto")
        try:
            library = getattr(self, "style_library", None) or StyleLibrary()
            profile = library.load(style_id)
        except Exception:
            return style_id
        return f"{profile.name} [{profile.id}]"

    def _style_choices_for_language(self, language: str) -> tuple[str, ...]:
        """Return the implicit auto option plus profiles for one target language."""
        try:
            profiles = self.style_library.list(language)
        except (TypeError, ValueError):
            profiles = ()
        return ("auto",) + tuple(profile.id for profile in profiles)

    def _refresh_style_choices(self) -> None:
        """Keep the style selector compatible with the selected target language."""
        if not hasattr(self, "target_language_var") or not hasattr(self, "style_combo"):
            return
        self.style_choices = self._style_choices_for_language(self.target_language_var.get())
        self.style_display_choices = tuple(
            self._style_display(style_id) for style_id in self.style_choices
        )
        self.style_combo.configure(values=self.style_display_choices)
        self._set_style_value(self.style_var.get())

    def _set_style_value(self, style_id: Any) -> None:
        value = str(style_id or "auto").strip()
        choices = getattr(self, "style_choices", ("auto",))
        if value not in choices:
            value = "auto"
        if hasattr(self, "style_var"):
            self.style_var.set(value)
        if hasattr(self, "style_display_var"):
            self.style_display_var.set(self._style_display(value))

    def change_style(self, _event: Any = None) -> None:
        selected = self.style_display_var.get().strip()
        value = next(
            (
                style_id
                for style_id in getattr(self, "style_choices", ("auto",))
                if self._style_display(style_id) == selected
            ),
            "auto",
        )
        if self.form_editing:
            self.style_var.set(value)

    def change_target_language(self, _event: Any = None) -> None:
        """Refresh available explicit styles after a target-language change."""
        if not self.form_editing:
            return
        target = self.target_language_var.get().strip().lower()
        if target not in LANGUAGE_CHOICES:
            self.target_language_var.set("cs")
        self._refresh_style_choices()

    def refresh_models(self) -> None:
        if self.model_refreshing:
            return
        self.model_refreshing = True
        self.model_discovery = OllamaDiscovery("checking")
        self.labels["model_status"].configure(text=self._t("models_checking"))
        provider = self.provider_var.get().strip() or "ollama"

        def discover() -> None:
            try:
                if provider == "ollama":
                    result = discover_ollama_models()
                else:
                    from .ai import discover_profile_models
                    profile, _store = self._ensure_profile(provider)
                    models = discover_profile_models(profile)
                    result = OllamaDiscovery("available" if models else "empty", models=models)
            except Exception as exc:
                result = OllamaDiscovery("offline", detail=str(exc))
            try:
                self.root.after(0, lambda: self._apply_model_discovery(result))
            except Exception:
                pass

        threading.Thread(target=discover, name=f"{provider}-discovery", daemon=True).start()

    def _apply_model_discovery(self, discovery: OllamaDiscovery) -> None:
        self.model_refreshing = False
        self.model_discovery = discovery
        choices = list(discovery.models)
        for job in self.jobs_draft:
            model = job.get("model")
            if model and model not in choices:
                choices.append(model)
        current = self.model_var.get().strip()
        if current and current not in choices:
            choices.append(current)
        if not choices:
            choices = [DEFAULT_MODEL]
        self.model_choices = sorted(set(choices), key=str.casefold)
        self.model_combo.configure(values=tuple(self.model_choices))
        if current:
            self.model_var.set(current)
        self.labels["model_status"].configure(text=self._model_status_text())

    def _clear_job_detail(self) -> None:
        if "copy" in self.buttons:
            self.buttons["copy"].configure(state="disabled")
        self.provider_var.set("ollama")
        self.translator_var.set("basic")
        self.profile_var.set("")
        self.model_var.set(DEFAULT_MODEL)
        self.source_language_var.set("en")
        self.target_language_var.set("cs")
        self._refresh_style_choices()
        self._set_style_value("auto")
        self._set_phase_value("both")
        self.input_var.set("")
        self.output_var.set("")
        self.html_file_var.set("")

    def select_job(self, _event: Any = None) -> None:
        if self.form_editing:
            return
        job = self.selected_job()
        if not job:
            self._clear_job_detail()
            self._refresh_provider_controls()
            return
        self.buttons["copy"].configure(state="normal")
        self.provider_var.set(job.get("provider") or "ollama")
        self.translator_var.set(job.get("translator_id") or "basic")
        self.profile_var.set(job.get("profile") or "")
        self.model_var.set(job.get("model") or DEFAULT_MODEL)
        self.source_language_var.set(job.get("inlang") or "en")
        self.target_language_var.set(job.get("outlang") or "cs")
        self._refresh_style_choices()
        self._set_style_value(job.get("target_variant") or "auto")
        self._set_phase_value(job.get("phase") or "both")
        self.input_var.set(job.get("input") or "")
        self.output_var.set(job.get("output") or "")
        self.html_file_var.set(job.get("html_file") or "")
        self._refresh_provider_controls()

    def change_phase(self, _event: Any = None) -> None:
        selected = self.phase_display_var.get().strip()
        phase = next(
            (value for value in self.phase_choices if self._phase_display(value) == selected),
            "",
        )
        if not self.form_editing or phase not in self.phase_choices:
            return
        self.phase_var.set(phase)

    def choose_input(self) -> None:
        from tkinter import filedialog

        if not self.form_editing:
            return
        selected = filedialog.askopenfilename(
            title=self._t("input_file"),
            initialdir=str(self.workdir),
            filetypes=((self._t("pdf_files"), "*.pdf"), (self._t("all_files"), "*.*")),
        )
        if not selected:
            return
        source = Path(selected).expanduser().resolve()
        old_output = self.auto_output_suggestion
        old_html = self.auto_html_suggestion
        self.input_var.set(str(source))
        from .filename_policy import suggested_output

        target_language = self.target_language_var.get().strip() or "cs"
        output = suggested_output(source, target_language)
        html = output.with_suffix(".html")
        if not self.output_var.get().strip() or self.output_var.get() == old_output:
            self.output_var.set(str(output))
            self.auto_output_suggestion = str(output)
        if not self.html_file_var.get().strip() or self.html_file_var.get() == old_html:
            self.html_file_var.set(str(html))
            self.auto_html_suggestion = str(html)
        self.render()

    def choose_output(self) -> None:
        from tkinter import filedialog

        if not self.form_editing:
            return
        selected = filedialog.asksaveasfilename(
            title=self._t("output_file"),
            initialdir=str(self.workdir),
            defaultextension=".pdf",
            filetypes=((self._t("pdf_files"), "*.pdf"), (self._t("all_files"), "*.*")),
        )
        if not selected:
            return
        target = Path(selected).expanduser().resolve()
        old_html = self.auto_html_suggestion
        self.output_var.set(str(target))
        self.auto_output_suggestion = None
        if not self.html_file_var.get().strip() or self.html_file_var.get() == old_html:
            html = target.with_suffix(".html")
            self.html_file_var.set(str(html))
            self.auto_html_suggestion = str(html)

    def choose_html(self) -> None:
        from tkinter import filedialog

        if not self.form_editing:
            return
        selected = filedialog.askopenfilename(
            title=self._t("html_file"),
            initialdir=str(self.workdir),
            filetypes=(("HTML", "*.html *.htm"), (self._t("all_files"), "*.*")),
        )
        if not selected:
            return
        self.html_file_var.set(str(Path(selected).expanduser().resolve()))
        self._set_phase_value("pdf")
        self.render()

    def change_translator(self, _event: Any = None) -> None:
        if not self.form_editing:
            return
        if self.translator_var.get().strip() not in available_translation_module_ids():
            self.translator_var.set("basic")
        self._refresh_translation_controls()

    def change_provider(self, _event: Any = None) -> None:
        if not self.form_editing:
            return
        provider = self.provider_var.get().strip()
        if not provider:
            return
        self.profile_var.set("")
        self._refresh_provider_controls()

    def change_profile(self, _event: Any = None) -> None:
        if self.form_editing:
            return

    def change_model(self, _event: Any = None) -> None:
        if self.form_editing:
            return

    def _ensure_profile(self, provider: str):
        from .ai import AiProfile, ProfileStore
        store = ProfileStore(CONFIG_FILE)
        profile_id = self.profile_var.get().strip() or provider
        try:
            return store.get(profile_id), store
        except Exception:
            auth = "none" if provider == "ollama" else "api_key"
            credential = None if auth == "none" else f"env:{provider.upper()}_API_KEY"
            profile = AiProfile(
                profile_id, 1, provider, self.model_var.get().strip() or DEFAULT_MODEL,
                auth, credential,
            )
            store.save(profile)
            self.profile_var.set(profile_id)
            return profile, store

    def configure_provider(self) -> None:
        if not self.form_editing:
            return
        if not self._provider_options()["has_configuration"]:
            return
        from .gui.provider_dialogs import open_provider_dialog
        profile, store = self._ensure_profile(self.provider_var.get().strip() or "ollama")
        open_provider_dialog(
            self.root,
            profile,
            store,
            on_saved=lambda updated: self._apply_profile_update(updated),
            on_error=lambda action, exc: self._log_action(
                action,
                provider=profile.provider_id,
                profile=profile.profile_id,
                code=getattr(exc, "code", type(exc).__name__),
            ),
            translate=self._t,
        )

    def _apply_profile_update(self, profile) -> None:
        if not self.form_editing:
            return
        self.provider_var.set(profile.provider_id)
        self.profile_var.set(profile.profile_id)
        self.model_var.set(profile.model)
        self._refresh_provider_controls()
        self.render()

    def login_provider(self) -> None:
        if not self.form_editing:
            return
        provider = self.provider_var.get().strip()
        if not self._provider_options()["supports_login"]:
            return
        from .ai import (
            AiProfile,
            CredentialStoreUnavailable,
            GeminiOAuth,
            OAuthConfigurationError,
            credential_storage_status,
            credential_store_for,
            resolve_gemini_oauth_client_id,
        )
        profile, store = self._ensure_profile(provider)
        try:
            storage = credential_storage_status()
            if not storage.writable:
                self._log_action(
                    "provider.credentials.unavailable",
                    provider=provider,
                    profile=profile.profile_id,
                    backend=storage.backend,
                    code="credentials_unavailable",
                )
                self.messagebox.showerror(
                    self._t("login"),
                    storage.message + "\n\n" + storage.remedy,
                )
                return
            oauth_ref = f"oauth:{provider}:{profile.profile_id}"
            client_id = resolve_gemini_oauth_client_id(
                profile.options.get("oauth_client_id")
            )
            oauth = GeminiOAuth(
                credential_ref=oauth_ref,
                store=credential_store_for(),
                client_id=client_id,
            )
            oauth.login(True)
            updated = AiProfile(
                profile.profile_id, profile.revision + 1, profile.provider_id,
                profile.model, "oauth", oauth_ref, profile.options,
            )
            store.save(updated)
            self._apply_profile_update(updated)
            self.messagebox.showinfo(self._t("login"), self._t("login_completed"))
        except CredentialStoreUnavailable as exc:
            self._log_action(
                "provider.login.failed",
                provider=provider,
                profile=profile.profile_id,
                code=exc.code,
            )
            self.messagebox.showerror(
                self._t("login"),
                str(exc) + "\n\n" + exc.remedy,
            )
        except OAuthConfigurationError as exc:
            self._log_action(
                "provider.login.failed",
                provider=provider,
                profile=profile.profile_id,
                code=exc.code,
            )
            self.messagebox.showerror(
                self._t("login"),
                str(exc) + "\n\n" + exc.remedy,
            )
        except Exception as exc:
            self._log_action(
                "provider.login.failed",
                provider=provider,
                profile=profile.profile_id,
                code=type(exc).__name__,
            )
            self.messagebox.showerror(self._t("login"), str(exc))

    def selected_job(self) -> dict[str, Any] | None:
        selected = self.tree.selection()
        if not selected:
            return None
        job_id = selected[0]
        return next((job for job in self.jobs_draft if job["id"] == job_id), None)

    def render(self) -> None:
        """Refresh visible rows while preserving an existing job selection."""
        selection = self.tree.selection()
        selected_id = selection[0] if selection else None
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, job in enumerate(self.jobs_draft, 1):
            self.tree.insert(
                "", "end", iid=job["id"],
                values=(index, job["id"], self._t(job.get("state", "prepared")),
                        Path(job.get("input", "")).name, Path(job.get("output", "")).name,
                        job.get("model") or ""),
            )
        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)
        if not getattr(self, "form_editing", False) and hasattr(self, "select_job"):
            self.select_job()
        has_unsent = self._has_unsent_changes() if hasattr(self, "_has_unsent_changes") else self.dirty
        marker = self._t("unsent") if has_unsent else ""
        running = self.controller.running()
        stopping = self.controller.stopping()
        runtime_state = {}
        if (running or stopping) and hasattr(self.controller, "state_snapshot"):
            runtime_state = self.controller.state_snapshot()
        # Některé testovací/dummy GUI objekty nemají volitelný náhled.
        # Produkční QueueGui metodu vždy obsahuje, ale render musí zůstat
        # kompatibilní i s minimalistickými testovacími dvojníky.
        render_preview = getattr(self, "_render_preview", None)
        if render_preview is not None:
            render_preview(runtime_state)
        progress = runtime_state.get("progress")
        if hasattr(self, "progress"):
            value = float(progress) * 100 if isinstance(progress, (int, float)) else 0
            self.progress.configure(value=max(0, min(100, value)))
        if stopping:
            worker = self._t("stopping")
            self.buttons["stop"].configure(state="disabled")
        else:
            worker = self._t("running") if running else self._t("stopped")
            self.buttons["stop"].configure(state="normal")
            if running:
                detail = self._worker_activity_text(runtime_state)
                if detail:
                    worker = f"{worker}; {detail}"
        if getattr(self, "pending_delete_send", False):
            worker = f"{worker}; {self._t('delete_waiting')}"
        self.labels["status"].configure(
            text=self._t("status").format(
                worker=worker,
                revision=self.store.load().get("revision", 0), marker=marker
            )
        )

    def choose_workdir(self) -> None:
        from tkinter import filedialog

        selected = filedialog.askdirectory(
            title=self._t("choose_workdir"), initialdir=str(self.workdir)
        )
        if selected:
            self.workdir_var.set(selected)

    def apply_workdir(self) -> None:
        candidate = Path(self.workdir_var.get()).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        candidate = candidate.resolve()
        if not candidate.is_dir():
            self.messagebox.showerror(self._t("invalid_workdir"), str(candidate))
            return
        if self.controller.running():
            self.messagebox.showerror(self._t("worker_running"), self._t("stop_before_workdir"))
            return
        if self._has_unsent_changes() and not self.messagebox.askyesno(self._t("unsent_title"), self._t("discard_workdir")):
            return
        save_config(candidate, language=self.language)
        self.workdir = candidate
        self.queue_path = candidate / "queue.json"
        self.store = QueueStore(self.queue_path)
        self.controller = WorkerController(self.queue_path)
        self.jobs_draft = copy.deepcopy(self.store.jobs())
        snapshot = self.store.load()
        self.base_revision = snapshot.get("revision", 0)
        self.base_jobs = copy.deepcopy(self.jobs_draft)
        self.dirty = False
        self.form_editing = False
        self._set_job_form_state(False)
        self.workdir_var.set(str(candidate))
        self._log_action("workdir.changed", workdir=str(candidate))
        self.render()

    def add(self) -> None:
        """Begin a new local job draft; OK commits it to the GUI draft only."""
        if self.form_editing:
            return
        self.input_var.set("")
        self.output_var.set("")
        self.html_file_var.set("")
        self._set_phase_value("both")
        self.provider_var.set("ollama")
        self.profile_var.set("")
        self.model_var.set(DEFAULT_MODEL)
        self.source_language_var.set("en")
        self.target_language_var.set("cs")
        self._refresh_style_choices()
        self._set_style_value("auto")
        self.auto_output_suggestion = None
        self.auto_html_suggestion = None
        self.editing_job_template = None
        self._set_job_form_state(True)
        self._refresh_provider_controls()
        self._log_action("job.add.started")
        self.render()

    def copy_selected_job(self) -> None:
        """Open the selected job as a new editable draft without changing it."""
        if self.form_editing:
            return
        source = self.selected_job()
        if not source:
            return
        self.editing_job_template = copy.deepcopy(source)
        self.input_var.set(source.get("input") or "")
        self.output_var.set(source.get("output") or "")
        self.html_file_var.set(source.get("html_file") or "")
        self._set_phase_value(source.get("phase") or "both")
        self.provider_var.set(source.get("provider") or "ollama")
        self.profile_var.set(source.get("profile") or "")
        self.model_var.set(source.get("model") or DEFAULT_MODEL)
        if hasattr(self, "translator_var"):
            self.translator_var.set(source.get("translator_id") or "basic")
        if hasattr(self, "source_language_var"):
            self.source_language_var.set(source.get("inlang") or "en")
        if hasattr(self, "target_language_var"):
            self.target_language_var.set(source.get("outlang") or "cs")
        self._refresh_style_choices()
        self._set_style_value(source.get("target_variant") or "auto")
        self.auto_output_suggestion = None
        self.auto_html_suggestion = None
        self._set_job_form_state(True)
        self._refresh_provider_controls()
        self._log_action("job.copy.started", source_job_id=source["id"])
        self.render()

    def commit_job_form(self) -> None:
        """Validate and append the form to the local queue draft."""
        if not self.form_editing:
            return
        source_text = self.input_var.get().strip()
        output_text = self.output_var.get().strip()
        if not source_text:
            self.messagebox.showerror(self._t("input_file"), self._t("input_required"))
            return
        if not output_text:
            self.messagebox.showerror(self._t("output_file"), self._t("output_required"))
            return
        source = Path(source_text).expanduser().resolve()
        target = Path(output_text).expanduser().resolve()
        html_text = self.html_file_var.get().strip()
        if not source.is_file() or source.suffix.lower() != ".pdf":
            self.messagebox.showerror(self._t("input_file"), self._t("input_invalid"))
            return
        if target.suffix.lower() != ".pdf" or source == target:
            self.messagebox.showerror(self._t("output_file"), self._t("output_invalid"))
            return
        html_file = Path(html_text).expanduser().resolve() if html_text else None
        if html_file and html_file.suffix.lower() not in (".html", ".htm"):
            self.messagebox.showerror(self._t("html_file"), self._t("html_invalid"))
            return
        template = self.editing_job_template or {}
        source_language = (
            self.source_language_var.get().strip()
            if hasattr(self, "source_language_var")
            else template.get("inlang", "en")
        ) or template.get("inlang", "en")
        target_language = (
            self.target_language_var.get().strip()
            if hasattr(self, "target_language_var")
            else template.get("outlang", "cs")
        ) or template.get("outlang", "cs")
        target_variant = (
            self.style_var.get().strip()
            if hasattr(self, "style_var")
            else "auto"
        ) or "auto"
        if source_language == target_language and target_variant == "auto":
            self.messagebox.showerror(self._t("target_language"), self._t("same_language"))
            return
        job = make_job(
            source,
            target,
            inlang=source_language,
            outlang=target_language,
            model=self.model_var.get().strip() or None,
            translator_id=(
                self.translator_var.get().strip()
                if hasattr(self, "translator_var")
                else template.get("translator_id", "basic")
            ) or "basic",
            translator_options=template.get("translator_options") or {},
            provider=self.provider_var.get().strip() or "ollama",
            profile=self.profile_var.get().strip() or None,
            input_format=template.get("input_format"),
            output_format=template.get("output_format"),
            phase=self.phase_var.get().strip() or "both",
            target_variant=target_variant,
            html_file=html_file,
            first_page=template.get("first_page"),
            last_page=template.get("last_page"),
        )
        self.jobs_draft.append(job)
        self.editing_job_template = None
        self.dirty = True
        self._set_job_form_state(False)
        self._log_action("job.added", input=str(source), output=str(target), job_id=job["id"])
        self.render()
        self.tree.selection_set(job["id"])
        self.tree.focus(job["id"])
        self.select_job()

    def cancel_job_form(self) -> None:
        """Discard the uncommitted form without changing the queue draft."""
        if not self.form_editing:
            return
        self._set_job_form_state(False)
        self.editing_job_template = None
        self._log_action("job.add.cancelled")
        if self.selected_job() is not None:
            self.select_job()
        else:
            self._clear_job_detail()
            self._refresh_provider_controls()
        self.render()

    def move(self, delta: int) -> None:
        job = self.selected_job()
        if not job:
            return
        index = self.jobs_draft.index(job)
        target = index + delta
        if 0 <= target < len(self.jobs_draft):
            self.jobs_draft[index], self.jobs_draft[target] = self.jobs_draft[target], self.jobs_draft[index]
            self.dirty = True
            self._log_action("job.reordered", job_id=job["id"], delta=delta)
            self.render()
            self.tree.selection_set(job["id"])

    def prepare(self) -> None:
        job = self.selected_job()
        if job:
            job["state"] = "prepared"
            job["error"] = None
            self.dirty = True
            self._log_action("job.prepared", job_id=job["id"])
            self.render()

    def pause(self) -> None:
        job = self.selected_job()
        if job:
            job["state"] = "paused"
            self.dirty = True
            self._log_action("job.paused", job_id=job["id"])
            self.render()

    def delete(self) -> None:
        job = self.selected_job()
        if not job:
            return
        if not self.messagebox.askyesno(self._t("delete_title"), self._t("delete_confirm")):
            return
        self.jobs_draft = [item for item in self.jobs_draft if item["id"] != job["id"]]
        self.dirty = True
        self._log_action("job.deleted", job_id=job["id"])
        self.render()

    def _deleted_active_jobs(self) -> list[dict[str, Any]]:
        """Return current in-progress jobs removed from the GUI draft."""
        draft_ids = {job["id"] for job in self.jobs_draft}
        current_by_id = {job["id"]: job for job in self.store.jobs()}
        return [
            current
            for job_id, current in current_by_id.items()
            if job_id not in draft_ids and current.get("state") == "in_progress"
        ]

    def _publish_draft(self, *, allow_active_delete: bool = False) -> None:
        """Publish the draft and start the worker using the normal Update flow."""
        try:
            self.store.merge_jobs(
                self.jobs_draft,
                self.base_jobs,
                self.base_revision,
                allow_active_delete=allow_active_delete,
            )
        except QueueConflictError as exc:
            self.messagebox.showerror(self._t("unsent_title"), str(exc))
            return
        self.jobs_draft = copy.deepcopy(self.store.jobs())
        snapshot = self.store.load()
        self.base_revision = snapshot.get("revision", 0)
        self.base_jobs = copy.deepcopy(self.jobs_draft)
        self.dirty = False
        self.controller.start()
        self._log_action("update", allow_active_delete=allow_active_delete)
        self.render()

    def send(self) -> None:
        """Publish GUI edits; the worker cancels only if its job is invalidated."""
        active_deletions = self._deleted_active_jobs()
        if active_deletions and self.controller.running():
            if not self.messagebox.askyesno(
                self._t("delete_active_title"),
                self._t("delete_active_confirm"),
            ):
                return
            self._log_action(
                "job.delete_active.confirmed",
                job_ids=[job["id"] for job in active_deletions],
            )
        self.controller.cancel_stop()
        self._publish_draft(allow_active_delete=bool(active_deletions))

    def start(self) -> None:
        self.controller.start()
        self._log_action("start")
        self.render()

    def stop(self) -> None:
        self.controller.stop()
        self._log_action("stop")
        self.render()

    def change_language(self, _event: Any = None) -> None:
        selected = self.language_var.get()
        if selected not in GUI_TEXT:
            return
        self.language = selected
        save_config(self.workdir, language=self.language)
        self._log_action("language.changed", language=self.language)
        self.refresh_labels()
        self.render()

    def refresh(self) -> None:
        if self._has_unsent_changes():
            if not self.messagebox.askyesno(self._t("unsent_title"), self._t("discard")):
                return
            if self.form_editing:
                self.cancel_job_form()
        self.jobs_draft = copy.deepcopy(self.store.jobs())
        snapshot = self.store.load()
        self.base_revision = snapshot.get("revision", 0)
        self.base_jobs = copy.deepcopy(self.jobs_draft)
        self.dirty = False
        self._refresh_provider_controls()
        self.refresh_models()
        self._log_action("refresh")
        self.render()

    def poll(self) -> None:
        """Poll runtime state without replacing a user-owned dirty draft."""
        if not self._has_unsent_changes():
            self.jobs_draft = copy.deepcopy(self.store.jobs())
            snapshot = self.store.load()
            self.base_revision = snapshot.get("revision", 0)
            self.base_jobs = copy.deepcopy(self.jobs_draft)
        self.render()
        self.root.after(700, self.poll)

    def close(self) -> None:
        if self._has_unsent_changes() and not self.messagebox.askyesno(self._t("unsent_title"), self._t("close_unsent")):
            return
        self.root.destroy()


def gui_main(queue_path: Path | None = None) -> None:
    QueueGui(queue_path).root.mainloop()
