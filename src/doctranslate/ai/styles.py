"""Built-in translation style profiles and their validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.resources
import json
from typing import Any, Mapping

from .contracts import normalize_language


class StyleError(ValueError):
    """Raised when a style catalog or style selection is invalid."""


@dataclass(frozen=True)
class StylePromptRules:
    """Prompt constraints supplied by an explicit style profile."""

    must: tuple[str, ...] = ()
    should: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()


@dataclass(frozen=True)
class StylePolicy:
    """Machine-readable policy used by prompt composition and validation."""

    register: str
    period: str
    expressivity: str
    vulgarity: str
    fidelity: str
    caricature_intensity: int = 0
    target_language_guard: bool = True
    transformation: str = "none"
    lexical_expansion: bool = False


@dataclass(frozen=True)
class StyleProfile:
    """Immutable, serializable description of one explicit style variant."""

    id: str
    name: str
    language: str
    description: str
    version: str
    prompt: StylePromptRules
    policy: StylePolicy
    style_samples: tuple[str, ...]
    lexicon: tuple[str, ...]
    transformations: tuple[str, ...]
    references: tuple[str, ...]
    provenance: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "StyleProfile":
        if not isinstance(value, Mapping):
            raise StyleError("Style profile must be an object")

        def required_text(name: str) -> str:
            item = value.get(name)
            if not isinstance(item, str) or not item.strip():
                raise StyleError(f"Style profile field {name!r} must be non-empty text")
            return item.strip()

        def text_tuple(
            container: Mapping[str, Any], name: str, required: bool = False
        ) -> tuple[str, ...]:
            item = container.get(name)
            if item is None and not required:
                return ()
            if not isinstance(item, list) or any(
                not isinstance(entry, str) or not entry.strip() for entry in item
            ):
                raise StyleError(
                    f"Style profile field {name!r} must be a list of non-empty strings"
                )
            return tuple(entry.strip() for entry in item)

        prompt_value = value.get("prompt")
        if not isinstance(prompt_value, Mapping):
            raise StyleError("Style profile field 'prompt' must be an object")
        policy_value = value.get("policy")
        if not isinstance(policy_value, Mapping):
            raise StyleError("Style profile field 'policy' must be an object")

        profile_id = required_text("id")
        policy = StylePolicy(
            register=required_policy_text(policy_value, "register"),
            period=required_policy_text(policy_value, "period"),
            expressivity=required_policy_text(policy_value, "expressivity"),
            vulgarity=required_policy_text(policy_value, "vulgarity"),
            fidelity=required_policy_text(policy_value, "fidelity"),
            caricature_intensity=policy_value.get("caricature_intensity", 0),
            target_language_guard=policy_value.get("target_language_guard", True),
            transformation=policy_value.get("transformation", "none"),
            lexical_expansion=policy_value.get("lexical_expansion", False),
        )
        _validate_policy(policy, profile_id)
        return cls(
            id=profile_id,
            name=required_text("name"),
            language=normalize_language(required_text("language")),
            description=required_text("description"),
            version=required_text("version"),
            prompt=StylePromptRules(
                must=text_tuple(prompt_value, "must"),
                should=text_tuple(prompt_value, "should"),
                avoid=text_tuple(prompt_value, "avoid"),
                forbidden=text_tuple(prompt_value, "forbidden"),
            ),
            policy=policy,
            style_samples=text_tuple(value, "style_samples", required=True),
            lexicon=text_tuple(value, "lexicon"),
            transformations=text_tuple(value, "transformations"),
            references=text_tuple(value, "references", required=True),
            provenance=required_text("provenance"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "description": self.description,
            "version": self.version,
            "prompt": {
                "must": list(self.prompt.must),
                "should": list(self.prompt.should),
                "avoid": list(self.prompt.avoid),
                "forbidden": list(self.prompt.forbidden),
            },
            "policy": {
                "register": self.policy.register,
                "period": self.policy.period,
                "expressivity": self.policy.expressivity,
                "vulgarity": self.policy.vulgarity,
                "fidelity": self.policy.fidelity,
                "caricature_intensity": self.policy.caricature_intensity,
                "target_language_guard": self.policy.target_language_guard,
                "transformation": self.policy.transformation,
                "lexical_expansion": self.policy.lexical_expansion,
            },
            "style_samples": list(self.style_samples),
            "lexicon": list(self.lexicon),
            "transformations": list(self.transformations),
            "references": list(self.references),
            "provenance": self.provenance,
        }


def required_policy_text(value: Mapping[str, Any], name: str) -> str:
    item = value.get(name)
    if not isinstance(item, str) or not item.strip():
        raise StyleError(f"Style policy field {name!r} must be non-empty text")
    return item.strip()


def _validate_policy(policy: StylePolicy, profile_id: str) -> None:
    if policy.vulgarity not in {"avoid", "preserve-if-present", "allow"}:
        raise StyleError(f"Invalid vulgarity policy for {profile_id}: {policy.vulgarity!r}")
    if policy.fidelity not in {
        "preserve-meaning",
        "preserve-meaning-and-intensity",
        "soften",
    }:
        raise StyleError(f"Invalid fidelity policy for {profile_id}: {policy.fidelity!r}")
    if policy.transformation not in {
        "none",
        "register-shift",
        "stylistic-rewrite",
        "regional-caricature",
    }:
        raise StyleError(
            f"Invalid transformation policy for {profile_id}: {policy.transformation!r}"
        )
    if not isinstance(policy.caricature_intensity, int) or not 0 <= policy.caricature_intensity <= 3:
        raise StyleError(
            f"Caricature intensity for {profile_id} must be an integer from 0 to 3"
        )
    if not isinstance(policy.target_language_guard, bool):
        raise StyleError(f"Target-language guard for {profile_id} must be boolean")
    if not isinstance(policy.lexical_expansion, bool):
        raise StyleError(f"Lexical-expansion flag for {profile_id} must be boolean")
    if (
        policy.vulgarity == "avoid"
        and policy.fidelity == "preserve-meaning-and-intensity"
    ):
        raise StyleError(f"Conflicting vulgarity and fidelity policies for {profile_id}")


class StyleLibrary:
    """Read-only catalog of built-in explicit styles."""

    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        if payload is None:
            raw = (
                importlib.resources.files("doctranslate.ai.data")
                .joinpath("styles.json")
                .read_text(encoding="utf-8")
            )
            payload = json.loads(raw)
        if not isinstance(payload, Mapping) or not isinstance(payload.get("profiles"), list):
            raise StyleError("Style catalog must contain a profiles list")
        profiles = tuple(StyleProfile.from_dict(item) for item in payload["profiles"])
        self._profiles = self._validate_unique(profiles)

    @staticmethod
    def _validate_unique(profiles: tuple[StyleProfile, ...]) -> tuple[StyleProfile, ...]:
        ids = [profile.id for profile in profiles]
        if len(ids) != len(set(ids)):
            raise StyleError("Style catalog contains duplicate profile ids")
        return tuple(sorted(profiles, key=lambda profile: profile.id))

    def validate_all(self) -> tuple[str, ...]:
        """Return the validated stable profile order."""
        return tuple(profile.id for profile in self._profiles)

    def list(self, language: str | None = None) -> tuple[StyleProfile, ...]:
        if language is None or not language.strip():
            return self._profiles
        normalized = normalize_language(language)
        return tuple(profile for profile in self._profiles if profile.language == normalized)

    def load(self, style_id: str) -> StyleProfile:
        if style_id == "auto":
            raise StyleError("'auto' is implicit and has no explicit style profile")
        for profile in self._profiles:
            if profile.id == style_id:
                return profile
        raise StyleError(f"Unknown style profile: {style_id!r}")

    def fingerprint(self, style_id: str) -> str:
        """Return a stable hash of the effective profile content."""

        if style_id == "auto":
            return "auto-v1"
        payload = json.dumps(
            self.load(style_id).to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def resolve_variant(self, value: str | None, target_language: str) -> str:
        if value is None or not value.strip() or value.strip().lower() == "auto":
            return "auto"
        normalized = normalize_language(target_language)
        profile = self.load(value.strip())
        if profile.language != normalized:
            raise StyleError(
                f"Style {profile.id!r} targets {profile.language}, not {normalized}"
            )
        return profile.id


def compose_policy(
    source_language: str,
    target_language: str,
    variant: str | None = None,
    *,
    library: StyleLibrary | None = None,
) -> str:
    """Create trusted style instructions without mixing them with document data.

    The auto variant deliberately contains no built-in sample. It preserves
    the source author's register and expressivity instead.
    """

    source = normalize_language(source_language)
    target = normalize_language(target_language)
    selected = "auto" if variant is None or not variant.strip() else variant.strip()
    if selected.lower() == "auto":
        return (
            f"Translate from {source} to {target}. Do not impose a predefined "
            "style; preserve the source author's register, tone and expressivity."
        )

    profile = (library or StyleLibrary()).load(selected)
    if profile.language != target:
        raise StyleError(f"Style {profile.id!r} targets {profile.language}, not {target}")
    rules = profile.prompt
    lines = [
        f"Translate from {source} to {target} using style profile {profile.id}.",
        f"Style: {profile.name}. {profile.description}",
        f"Policy: register={profile.policy.register}; "
        f"fidelity={profile.policy.fidelity}; "
        f"vulgarity={profile.policy.vulgarity}.",
    ]
    for label, values in (
        ("Must", rules.must),
        ("Should", rules.should),
        ("Avoid", rules.avoid),
        ("Forbidden", rules.forbidden),
    ):
        if values:
            lines.append(f"{label}: " + " ".join(values))
    if profile.style_samples:
        lines.append("Style sample (pattern only, do not copy its content):")
        lines.extend(profile.style_samples)
    return "\n".join(lines)
