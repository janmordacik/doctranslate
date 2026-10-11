"""Production composition root for the standard translation engines.

The queue worker owns orchestration, while this module supplies the concrete
provider and the bridge between the format-neutral XHTML contract and the
existing high-fidelity PDF pipeline.
"""

from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from typing import Any, Callable

from ..ai.ollama import OllamaBackend
from ..translate_core.contracts import XhtmlBlock, XhtmlDocument
from .advanced import AdvancedTranslationEngine
from .checkpoint import JsonCheckpointStore
from .contracts import TranslationContext, TranslationError, TranslationOptions
from .memory import JsonGlossaryStore
from .registry import TranslationEngineRegistry, register_advanced_standard


BackendFactory = Callable[[dict[str, Any], Any], object]


def _default_backend_factory(job: dict[str, Any], translate_module: Any) -> object:
    """Create the local Ollama backend from one queue job."""
    provider = str(job.get("provider") or "ollama").strip().lower()
    if provider != "ollama":
        raise TranslationError(
            "provider_unsupported",
            f"Advanced production runner currently supports Ollama, got {provider!r}",
        )
    model = str(job.get("model") or getattr(translate_module, "DEFAULT_MODEL", "")).strip()
    if not model:
        raise TranslationError("model_missing", "Advanced translation requires a model")
    base_url = os.environ.get(
        "TRANSLATE_OLLAMA_URL",
        str(getattr(translate_module, "OLLAMA_URL", "http://localhost:11434")),
    )
    return OllamaBackend(model, base_url=base_url)


class ProductionTranslationRuntime:
    """Bind advanced translation to the worker's configured PDF job."""

    def __init__(
        self,
        worker: Any,
        translate_module: Any,
        *,
        backend_factory: BackendFactory = _default_backend_factory,
    ) -> None:
        self.worker = worker
        self.translate = translate_module
        self.backend_factory = backend_factory

    def registry(self) -> TranslationEngineRegistry:
        """Return the registry exposed by the production composition root."""
        result = TranslationEngineRegistry()
        register_advanced_standard(
            result,
            self._create_advanced_engine,
            reason="production advanced runner is not registered",
        )
        return result

    def _create_advanced_engine(
        self,
        dependencies: object,
        options: TranslationOptions,
    ) -> AdvancedTranslationEngine:
        """Create one isolated engine and persistent state for the current job."""
        if not isinstance(dependencies, dict):
            raise TranslationError("invalid_dependencies", "Worker dependencies must be a mapping")
        worker = dependencies.get("worker", self.worker)
        translate_module = dependencies.get("translate", self.translate)
        job = next(
            (item for item in worker.store.jobs() if item.get("id") == worker.current_job_id),
            None,
        )
        if job is None:
            raise TranslationError("job_missing", "Cannot create engine without the current job")
        backend = self.backend_factory(job, translate_module)
        output = Path(job["output"])
        state_prefix = output.with_name(output.name + ".advanced")
        return AdvancedTranslationEngine(
            backend,
            glossary_store=JsonGlossaryStore(
                state_prefix.with_name(state_prefix.name + ".glossary.json")
            ),
            checkpoint_store=JsonCheckpointStore(
                state_prefix.with_name(state_prefix.name + ".checkpoint.json")
            ),
        )

    def __call__(
        self,
        engine: AdvancedTranslationEngine,
        options: TranslationOptions,
        context: TranslationContext,
    ) -> None:
        """Translate XHTML fragments, write HTML, and optionally typeset PDF."""
        if self.translate.PHASE not in {"html", "both"}:
            raise TranslationError(
                "invalid_phase",
                "The advanced engine must receive html or both; pdf is render-only",
            )
        self.translate.configure_run_logging()
        with self.translate.fitz.open(self.translate.INPUT_PDF) as source:
            identity = self.translate.job_identity(source, self.translate.MODEL)
            groups = [
                (
                    page_number,
                    self.translate.extract_blocks(source, page_number),
                )
                for page_number in range(
                    self.translate.FIRST_PAGE - 1,
                    (
                        self.translate.LAST_PAGE
                        if self.translate.LAST_PAGE is not None
                        else len(source)
                    ),
                )
            ]
            metadata = self.translate.build_html_metadata(source, identity, groups)
            document, fragment_map = self._fragment_document(
                metadata,
                groups,
                identity,
            )
            result = engine.translate(document, options, context=context)
            cache = self._restore_legacy_markup(result.document, fragment_map)
            images = {
                page_number: self.translate.export_html_images(source, page_number)
                for page_number, _ in groups
            }
            self.translate.write_translation_html(
                metadata,
                groups,
                images,
                cache,
                {},
            )
        context.logger(
            "worker.translation.engine.completed",
            translator_id="advanced",
            metrics=result.metrics,
            warnings=result.warnings,
        )
        if self.translate.PHASE == "both":
            self.translate.set_activity("typesetting", phase="pdf", unit="pages")
            self.translate.run_html_typesetting(context.cancel_event)

    def _fragment_document(
        self,
        metadata: dict[str, Any],
        groups: list[tuple[int, list[dict[str, Any]]]],
        identity: dict[str, Any],
    ) -> tuple[XhtmlDocument, dict[str, tuple[dict[str, Any], tuple, str]]]:
        """Expose each legacy text span as a stable XHTML translation block."""
        base = self.translate.xhtml_document_from_page_groups(metadata, groups)
        base = replace(
            base,
            metadata=replace(
                base.metadata,
                source_sha256=identity.get("source_hash"),
            ),
        )
        fragments: list[XhtmlBlock] = []
        mapping: dict[str, tuple[dict[str, Any], tuple, str]] = {}
        for page_number, blocks in groups:
            for order, block in enumerate(blocks):
                legacy_id = self.translate.block_id(page_number, order)
                prepared = self.translate.prepare_text_translation(block)
                texts = prepared[0]
                for span_id, text in texts.items():
                    fragment_id = f"{legacy_id}::{span_id}"
                    fragments.append(
                        XhtmlBlock(
                            block_id=fragment_id,
                            page_number=page_number + 1,
                            order=order,
                            text=text,
                            markup="",
                            bbox=tuple(block["bbox"]) if block.get("bbox") else None,
                            style=dict(block.get("styles", {})),
                            attributes={
                                "legacy_block_id": legacy_id,
                                "legacy_span_id": span_id,
                            },
                        )
                    )
                mapping[legacy_id] = (block, prepared, legacy_id)
        return base.with_blocks(tuple(fragments)), mapping

    def _restore_legacy_markup(
        self,
        document: XhtmlDocument,
        mapping: dict[str, tuple[dict[str, Any], tuple, str]],
    ) -> dict[str, str]:
        """Reassemble translated spans so the existing PDF typesetter can use them."""
        translated = document.block_map()
        cache: dict[str, str] = {}
        for legacy_id, (block, prepared, _) in mapping.items():
            texts = prepared[0]
            values = {
                span_id: translated[f"{legacy_id}::{span_id}"].text
                for span_id in texts
            }
            markup = (
                self.translate.restore_text_translation(values, block, prepared)
                if values
                else block["markup"]
            )
            cache[self.translate.cache_key(block)] = markup
        return cache


def build_worker_translation_runtime(
    worker: Any,
    translate_module: Any,
    *,
    backend_factory: BackendFactory = _default_backend_factory,
) -> tuple[TranslationEngineRegistry, Callable[..., None]]:
    """Build the registry and runner used by a production worker."""
    runtime = ProductionTranslationRuntime(
        worker,
        translate_module,
        backend_factory=backend_factory,
    )
    return runtime.registry(), runtime
