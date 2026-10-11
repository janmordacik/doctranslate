"""Standard bounded advanced translation engine without agent tool calling."""

from __future__ import annotations

from typing import Any

from doctranslate.ai.context_backend import ContextualRequest, require_contextual_capability
from doctranslate.ai.contracts import BackendError
from doctranslate.translate_core.contracts import XhtmlBlock, XhtmlDocument

from .checkpoint import CheckpointState, JsonCheckpointStore, ValidatedSegment, canonical_identity
from .context import ContextBudget, ContextBuilder
from .contracts import (
    TranslationCancelled,
    TranslationContext,
    TranslationEngine,
    TranslationError,
    TranslationMetrics,
    TranslationOptions,
    TranslationResult,
)
from .planning import PlanningBudget, PlannedSegment, SemanticBatchPlanner
from .retrieval import SourceOccurrence


ADVANCED_REVISION = "advanced-standard-v1"
ADVANCED_OPTIONS_SCHEMA = {
    "mode": str,
    "max_context_tokens": int,
    "instruction_tokens": int,
    "schema_tokens": int,
    "reserved_output_tokens": int,
    "max_attempts": int,
    "glossary_limit": int,
    "occurrence_limit": int,
    "quality_policy": str,
    "request_timeout": int,
    "manage_ollama": bool,
    "ollama_executable": str,
    "ollama_port": int,
    "ollama_context_length": int,
}


class AdvancedTranslationEngine:
    """Plan, enrich, translate and checkpoint bounded batches in one pass."""

    def __init__(
        self,
        backend: object,
        *,
        planner: SemanticBatchPlanner | None = None,
        context_builder: ContextBuilder | None = None,
        glossary_store: Any = None,
        checkpoint_store: Any = None,
        revision: str = ADVANCED_REVISION,
    ) -> None:
        self.backend = backend
        self.planner = planner or SemanticBatchPlanner()
        self.context_builder = context_builder or ContextBuilder()
        self.glossary_store = glossary_store
        self.checkpoint_store = checkpoint_store
        self.translator_id = "advanced"
        self.revision = revision

    def translate(
        self, document: XhtmlDocument, options: TranslationOptions,
        *, context: TranslationContext | None = None,
    ) -> TranslationResult:
        runtime = context or TranslationContext()
        limits = self._limits(options)
        require_contextual_capability(self.backend)
        planning_budget = PlanningBudget(
            limits["max_context_tokens"], limits["instruction_tokens"],
            limits["schema_tokens"], limits["reserved_output_tokens"],
        )
        plans = self.planner.plan(document.blocks, planning_budget)
        parts_by_block: dict[str, list[Any]] = {}
        for planned in plans:
            for part in planned.parts:
                parts_by_block.setdefault(part.source_block_id, []).append(part)
        identity = self._identity(document, options)
        checkpoint = self._load_checkpoint(identity)
        accepted = self._accepted_segments(checkpoint)
        memory = self.glossary_store.load() if self.glossary_store is not None else None
        translated = document
        warnings: list[str] = []
        completed = 0
        total = sum(1 for plan in plans for part in plan.parts if part.text.strip())
        batches = 0
        resumed_count = 0

        for plan in plans:
            self._check_cancel(runtime)
            parts = tuple(part for part in plan.parts if part.text.strip())
            known = tuple(
                part for part in parts
                if part.part_id in accepted and accepted[part.part_id].source_text == part.text
            )
            resumed_count += len(known)
            known_ids = {part.part_id for part in known}
            missing = tuple(part for part in parts if part.part_id not in known_ids)
            if known:
                translated = self._apply(translated, plan, accepted, parts_by_block)
            if missing:
                envelope = self.context_builder.build(
                    plan.input_text, options.source_language, options.target_language,
                    budget=ContextBudget(
                        limits["max_context_tokens"], limits["instruction_tokens"],
                        limits["schema_tokens"], limits["reserved_output_tokens"],
                    ),
                    memory=memory,
                    occurrences=self._occurrences(document, translated),
                    glossary_limit=limits["glossary_limit"],
                    occurrence_limit=limits["occurrence_limit"],
                )
                requests = tuple(
                    ContextualRequest(
                        part.part_id, part.text, options.source_language,
                        options.target_language, part.markup,
                        {"target_variant": options.target_variant},
                    )
                    for part in missing
                )
                results = self._translate_with_retry(requests, envelope, limits["max_attempts"], runtime)
                self._validate_quality(results, requests, limits["quality_policy"], warnings)
                for part, result in zip(missing, results):
                    accepted[part.part_id] = ValidatedSegment(
                        segment_id=part.part_id, source_text=part.text, text=result.text,
                        source_markup=part.markup, markup=result.markup or "",
                        term_bindings=tuple(item.entry.key for item in envelope.glossary),
                        provenance={"context_token_method": envelope.token_method},
                    )
                translated = self._apply(translated, plan, accepted, parts_by_block)
                batches += 1
                if runtime.on_batch_committed is not None:
                    runtime.on_batch_committed(tuple(part.source_block_id for part in missing))
                if runtime.on_preview is not None and results:
                    runtime.on_preview({
                        "stage": "translated", "block_id": missing[0].source_block_id,
                        "source_text": missing[0].text, "translated_text": results[0].text,
                    })
                self._save_checkpoint(identity, accepted, memory.revision if memory else None, batches, total)
            completed += len(parts)
            if runtime.on_progress is not None:
                runtime.on_progress(completed, total)

        self._check_cancel(runtime)
        return TranslationResult(
            translated,
            TranslationMetrics(
                translator_id=self.translator_id, translator_revision=self.revision,
                batches=batches, segments=total, resumed=resumed_count,
                ai_calls=batches,
                token_accounting={"context": "estimated"},
            ),
            tuple(warnings),
        )

    def _translate_with_retry(self, requests, envelope, max_attempts, context):
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            self._check_cancel(context)
            try:
                result = self.backend.translate_batch(requests, envelope)
                if len(result) != len(requests):
                    raise TranslationError("invalid_result", "Advanced backend returned an incomplete batch")
                return tuple(result)
            except TranslationCancelled:
                raise
            except BackendError as exc:
                if exc.code == "cancelled":
                    raise TranslationCancelled(str(exc)) from exc
                if exc.code == "request_timeout":
                    if context.logger is not None:
                        context.logger(
                            "worker.translation.request_timeout",
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            error=str(exc),
                        )
                    if attempt + 1 >= max_attempts:
                        raise TranslationError(
                            "request_timeout",
                            str(exc),
                            retryable=False,
                        ) from exc
                    continue
                last_error = exc
                if not exc.retryable or attempt + 1 >= max_attempts:
                    raise TranslationError("backend_error", str(exc), retryable=False) from exc
            except Exception as exc:
                last_error = exc
                if not getattr(exc, "retryable", False) or attempt + 1 >= max_attempts:
                    if isinstance(exc, TranslationError):
                        raise
                    raise TranslationError("backend_error", str(exc), retryable=False) from exc
        raise TranslationError("backend_error", str(last_error or "advanced backend failed"))

    @staticmethod
    def _validate_quality(results, requests, policy: str, warnings: list[str]) -> None:
        for request, result in zip(requests, results):
            if not isinstance(result.text, str) or not result.text.strip():
                raise TranslationError("invalid_result", f"Empty advanced result: {result.segment_id}")
            if result.text.strip() == request.text.strip():
                message = f"Result appears unchanged for segment {result.segment_id}"
                if policy == "strict":
                    raise TranslationError("quality_warning", message)
                warnings.append(message)

    @staticmethod
    def _apply(
        document: XhtmlDocument, plan: PlannedSegment,
        accepted: dict[str, ValidatedSegment], parts_by_block: dict[str, list[Any]],
    ) -> XhtmlDocument:
        by_block: dict[str, list[ValidatedSegment]] = {}
        for block_id in plan.source_block_ids:
            for part in parts_by_block.get(block_id, plan.parts):
                value = accepted.get(part.part_id)
                if value is not None:
                    by_block.setdefault(block_id, []).append(value)
        replacements: dict[str, XhtmlBlock] = {}
        for block_id, values in by_block.items():
            block = document.block_map()[block_id]
            text = "".join(value.text for value in values)
            markup = values[0].markup if len(values) == 1 and values[0].markup else block.markup
            replacements[block_id] = block.translated(text, markup)
        return document.with_blocks(tuple(replacements.get(block.block_id, block) for block in document.blocks))

    def _load_checkpoint(self, identity: str):
        if self.checkpoint_store is None:
            return None
        return self.checkpoint_store.load(expected_identity=identity)

    def _save_checkpoint(self, identity, accepted, memory_revision, batches, total) -> None:
        if self.checkpoint_store is None:
            return
        values = tuple(accepted[key] for key in sorted(accepted))
        self.checkpoint_store.save(CheckpointState(
            identity=identity, validated_segments=values,
            used_memory_revision=str(memory_revision) if memory_revision is not None else None,
            counters={"batches": batches, "segments": total},
        ))

    @staticmethod
    def _accepted_segments(checkpoint) -> dict[str, ValidatedSegment]:
        if checkpoint is None:
            return {}
        return {item.segment_id: item for item in checkpoint.validated_segments}

    @staticmethod
    def _occurrences(original: XhtmlDocument, translated: XhtmlDocument) -> tuple[SourceOccurrence, ...]:
        return tuple(
            SourceOccurrence(block.block_id, block.text, translated.block_map()[block.block_id].text, block.page_number)
            for block in original.blocks
            if translated.block_map()[block.block_id].text != block.text
        )

    @staticmethod
    def _identity(document: XhtmlDocument, options: TranslationOptions) -> str:
        source = {
            "path": document.metadata.source_path,
            "sha256": document.metadata.source_sha256,
            "blocks": [{"id": block.block_id, "text": block.text} for block in document.blocks],
        }
        return canonical_identity(
            source=source, translator_id="advanced", translator_revision=ADVANCED_REVISION,
            options=options, segment_policy="advanced-standard-v1",
        )

    @staticmethod
    def _limits(options: TranslationOptions) -> dict[str, Any]:
        values = options.translator_options
        limits = {
            "max_context_tokens": values.get("max_context_tokens", 8192),
            "instruction_tokens": values.get("instruction_tokens", 256),
            "schema_tokens": values.get("schema_tokens", 128),
            "reserved_output_tokens": values.get("reserved_output_tokens", 1024),
            "max_attempts": values.get("max_attempts", 2),
            "glossary_limit": values.get("glossary_limit", 8),
            "occurrence_limit": values.get("occurrence_limit", 4),
            "quality_policy": values.get("quality_policy", "warn"),
            "request_timeout": values.get("request_timeout", 1800),
            "manage_ollama": values.get("manage_ollama", True),
            "ollama_executable": values.get("ollama_executable", "ollama"),
            "ollama_port": values.get("ollama_port", 11435),
            "ollama_context_length": values.get("ollama_context_length"),
        }
        for name, value in limits.items():
            if name in {"quality_policy", "manage_ollama", "ollama_executable"}:
                continue
            if name == "ollama_context_length" and value is None:
                continue
            if type(value) is not int or value < 1:
                raise TranslationError("invalid_options", f"{name} must be a positive integer")
        if limits["quality_policy"] not in {"warn", "strict"}:
            raise TranslationError("invalid_options", "quality_policy must be warn or strict")
        if not isinstance(limits["manage_ollama"], bool):
            raise TranslationError("invalid_options", "manage_ollama must be boolean")
        if not isinstance(limits["ollama_executable"], str) or not limits["ollama_executable"].strip():
            raise TranslationError("invalid_options", "ollama_executable must be a non-empty string")
        return limits

    @staticmethod
    def _check_cancel(context: TranslationContext) -> None:
        if context.cancel_event is not None and context.cancel_event.is_set():
            raise TranslationCancelled()
