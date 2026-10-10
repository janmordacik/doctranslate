"""Versioned non-secret AI provider profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import threading
from typing import Any, Mapping


PROFILE_SCHEMA = 2
_SECRET_KEYS = {"api_key", "token", "secret", "password", "access_token", "refresh_token"}


class ProfileError(ValueError):
    """A profile cannot be loaded or safely persisted."""


@dataclass(frozen=True)
class AiProfile:
    """Non-secret provider selection and authentication references."""

    profile_id: str
    revision: int
    provider_id: str
    model: str
    auth_type: str = "none"
    credential_ref: str | None = None
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.profile_id or self.revision < 1 or not self.provider_id or not self.model:
            raise ProfileError("profile_id, positive revision, provider_id and model are required")
        if self.auth_type not in {"none", "api_key", "oauth"}:
            raise ProfileError(f"Unsupported auth type: {self.auth_type}")
        if self.auth_type != "none" and not self.credential_ref:
            raise ProfileError("Authenticated profiles require credential_ref")
        if any(str(key).lower() in _SECRET_KEYS for key in self.options):
            raise ProfileError("Secrets must be stored in CredentialStore, not profile options")

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration without resolving or embedding credentials."""
        return {
            "id": self.profile_id,
            "revision": self.revision,
            "provider": self.provider_id,
            "model": self.model,
            "auth": self.auth_type,
            "credential_ref": self.credential_ref,
            "options": dict(self.options),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AiProfile":
        """Validate and load one persisted profile record."""
        try:
            return cls(
                profile_id=str(value["id"]),
                revision=int(value["revision"]),
                provider_id=str(value["provider"]),
                model=str(value["model"]),
                auth_type=str(value.get("auth", "none")),
                credential_ref=value.get("credential_ref"),
                options=value.get("options", {}),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ProfileError):
                raise
            raise ProfileError(f"Invalid AI profile: {exc}") from exc


class ProfileStore:
    """Atomic profile repository sharing the project configuration file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self._lock = threading.RLock()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema": PROFILE_SCHEMA, "profiles": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProfileError(f"Cannot read profile configuration {self.path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ProfileError("Profile configuration must be an object")
        if value.get("schema") not in (None, 1, PROFILE_SCHEMA):
            raise ProfileError("Unsupported profile configuration schema")
        profiles = value.get("profiles", [])
        if not isinstance(profiles, list):
            raise ProfileError("profiles must be a list")
        # Schema 1 configurations predate provider profiles. Normalize them
        # in memory so list(), get() and save() can use one stable shape.
        value["profiles"] = profiles
        return value

    def list(self) -> tuple[AiProfile, ...]:
        """Return all profiles in stable profile/revision order."""
        with self._lock:
            value = self._load()
            result = tuple(AiProfile.from_dict(item) for item in value["profiles"])
        if len({(item.profile_id, item.revision) for item in result}) != len(result):
            raise ProfileError("Duplicate profile id/revision")
        return tuple(sorted(result, key=lambda item: (item.profile_id, item.revision)))

    def get(self, profile_id: str, revision: int | None = None) -> AiProfile:
        """Return the requested revision or the newest revision by default."""
        candidates = [item for item in self.list() if item.profile_id == profile_id]
        if revision is not None:
            candidates = [item for item in candidates if item.revision == revision]
        if not candidates:
            raise ProfileError(f"Unknown AI profile {profile_id!r}")
        return max(candidates, key=lambda item: item.revision)

    def save(self, profile: AiProfile) -> AiProfile:
        """Atomically save a revision while preserving unrelated configuration keys."""
        with self._lock:
            value = self._load()
            profiles = [item for item in value["profiles"] if not (
                item.get("id") == profile.profile_id and int(item.get("revision", 0)) == profile.revision
            )]
            profiles.append(profile.to_dict())
            value["schema"] = PROFILE_SCHEMA
            value["profiles"] = profiles
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(self.path.name + ".tmp")
            temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.path)
        return profile
