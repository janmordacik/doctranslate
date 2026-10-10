"""Project-local configuration for the translation work directory and GUI."""

from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Any


# Keep installed packages read-only: by default configuration belongs to the
# current project/work directory, with an explicit environment override.
CONFIG_FILE = Path(
    os.environ.get("TRANSLATE_CONFIG_FILE", Path.cwd() / "translate.config.json")
).expanduser().resolve()
CONFIG_SCHEMA = 2
SUPPORTED_CONFIG_SCHEMAS = (1, CONFIG_SCHEMA)
SUPPORTED_LANGUAGES = ("cs", "en")


class ConfigError(RuntimeError):
    """The configured file exists but cannot be used safely."""



def load_config(path: Path = CONFIG_FILE) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Cannot read configuration {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in configuration {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"Configuration root must be an object: {path}")
    if value.get("schema") not in (None, *SUPPORTED_CONFIG_SCHEMAS):
        raise ConfigError(f"Unsupported configuration schema in {path}")
    return value


def get_workdir(path: Path = CONFIG_FILE, fallback: Path | None = None) -> Path:
    fallback = Path.cwd() if fallback is None else Path(fallback)
    value = load_config(path).get("workdir")
    if not isinstance(value, str) or not value.strip():
        return fallback.expanduser().resolve()
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path(path).resolve().parent / candidate
    return candidate.resolve()


def detect_language() -> str:
    """Return Czech for Czech locales and English otherwise."""
    try:
        language = (locale.getlocale()[0] or "").lower()
    except ValueError:
        language = ""
    is_czech = language.startswith("cs") or "czech" in language or "cesky" in language or "češt" in language
    return "cs" if is_czech else "en"


def get_language(path: Path = CONFIG_FILE, fallback: str | None = None) -> str:
    value = load_config(path).get("language")
    if isinstance(value, str) and value in SUPPORTED_LANGUAGES:
        return value
    return fallback if fallback in SUPPORTED_LANGUAGES else detect_language()


def save_config(
    workdir: Path | None = None,
    path: Path = CONFIG_FILE,
    *,
    language: str | None = None,
) -> Path:
    path = Path(path)
    existing = load_config(path)
    selected_workdir = get_workdir(path) if workdir is None else Path(workdir)
    selected_language = language or existing.get("language") or detect_language()
    if selected_language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported GUI language: {selected_language}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve provider profiles and future non-secret settings.  The GUI
    # owns only these two fields and must not erase another component's data.
    value = dict(existing)
    value.update({
        "schema": CONFIG_SCHEMA,
        "workdir": str(selected_workdir.expanduser().resolve()),
        "language": selected_language,
    })
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path
