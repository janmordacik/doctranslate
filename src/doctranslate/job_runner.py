"""Format/provider-neutral job orchestration with restartable checkpoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import threading
from typing import Callable

from .ai.contracts import AiBackend, SegmentRequest
from .ai.translation import SegmentTranslationPipeline
from .formats.registry import FormatRegistry
from .translate_core.contracts import XhtmlDocument


@dataclass(frozen=True)
class JobSpec:
    """Immutable job contract shared by adapters, translation and checkpoints."""

    job_id: str
    input_path: Path
    output_path: Path
    source_language: str
    target_language: str
    input_format: str | None = None
    output_format: str | None = None
    provider_id: str = "ollama"
    profile_id: str | None = None
    model: str = ""
    phase: str = "both"
    prompt_revision: str = "translate-segments-v1"
    segment_policy: str = "block-v1"


@dataclass(frozen=True)
class RunContext:
    """Runtime controls that may change while a job is executing."""

    workdir: Path
    cancel_event: threading.Event | None = None
    checkpoint_path: Path | None = None


@dataclass(frozen=True)
class JobResult:
    """Stable summary returned after a job completes or resumes."""

    job_id: str
    output_path: Path
    translated_blocks: int
    resumed_blocks: int


class JobRunner:
    """Run one job through selected format adapters and an AI backend."""

    def __init__(self, formats: FormatRegistry, *, logger: Callable[..., None] | None = None):
        self.formats = formats
        self.logger = logger or (lambda *_args, **_kwargs: None)

    @staticmethod
    def identity(spec: JobSpec, document: XhtmlDocument | None = None) -> str:
        """Hash all inputs that make a checkpoint safe to reuse."""
        source_hash = document.metadata.source_sha256 if document else None
        payload = {
            "input": str(spec.input_path.resolve()),
            "output": str(spec.output_path.resolve()),
            "source_language": spec.source_language,
            "target_language": spec.target_language,
            "input_format": spec.input_format,
            "output_format": spec.output_format,
            "provider": spec.provider_id,
            "profile": spec.profile_id,
            "model": spec.model,
            "prompt_revision": spec.prompt_revision,
            "segment_policy": spec.segment_policy,
            "source_sha256": source_hash,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def _load_checkpoint(path: Path | None, identity: str) -> dict[str, str]:
        if path is None or not path.is_file():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if value.get("identity") != identity:
            return {}
        translations = value.get("translations", {})
        return dict(translations) if isinstance(translations, dict) else {}

    @staticmethod
    def _save_checkpoint(path: Path | None, identity: str, completed: dict[str, str]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps({
            "schema": 1,
            "identity": identity,
            "completed_blocks": sorted(completed),
            "translations": completed,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def run(
        self,
        spec: JobSpec,
        context: RunContext,
        *,
        backend: AiBackend | None = None,
    ) -> JobResult:
        input_adapter = self.formats.create("input", spec.input_path, spec.input_format)
        output_adapter = self.formats.create("output", spec.output_path, spec.output_format)
        document = input_adapter.read(spec.input_path)
        # A checkpoint is valid only for the same source, provider, model and
        # prompt policy; otherwise an old translation could silently leak in.
        identity = self.identity(spec, document)
        completed = self._load_checkpoint(context.checkpoint_path, identity)
        resumed = len(completed)
        self.logger("job.input.loaded", job_id=spec.job_id, identity=identity)

        if spec.phase in {"html", "both"}:
            if backend is None:
                raise RuntimeError("A translation backend is required for HTML/both phase")
            requests = [
                SegmentRequest(
                    block.block_id,
                    block.text,
                    spec.source_language,
                    spec.target_language,
                )
                for block in document.blocks
                if block.text.strip() and block.block_id not in completed
            ]
            results = SegmentTranslationPipeline(backend).translate(
                requests, cancel_event=context.cancel_event
            )
            values = {item.segment_id: item.text for item in results}
            document = document.with_blocks([
                block.translated(completed[block.block_id]) if block.block_id in completed else block
                for block in document.blocks
            ])
            completed.update(values)
            self._save_checkpoint(context.checkpoint_path, identity, completed)
            self.logger("job.translation.checkpoint", job_id=spec.job_id, blocks=len(completed))

        if spec.phase in {"pdf", "both"}:
            # The output adapter receives the translated XHTML document, not
            # provider-specific response data. This keeps formatting separate.
            output_adapter.write(document, spec.output_path)
        return JobResult(spec.job_id, Path(spec.output_path), len(completed), resumed)
