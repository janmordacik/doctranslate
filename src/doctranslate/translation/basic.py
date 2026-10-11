"""Basic linear translation engine over injected batch execution."""

from __future__ import annotations

from typing import Any, Callable, Protocol, Sequence

from doctranslate.ai.contracts import SegmentRequest, SegmentResult
from doctranslate.ai.translation import validate_segment_results
from doctranslate.translate_core.contracts import XhtmlBlock, XhtmlDocument
from doctranslate.translate_core.pipeline import translated_markup
from .contracts import (
    TranslationContext,
    TranslationEngine,
    TranslationError,
    TranslationMetrics,
    TranslationOptions,
    TranslationResult,
    TranslationCancelled,
)


class BatchExecutor(Protocol):
    """Execute one ordered batch without knowing document or PDF formats."""

    def execute(
        self,
        requests: Sequence[SegmentRequest],
        options: TranslationOptions,
        *,
        context: TranslationContext,
    ) -> Sequence[SegmentResult]:
        """Return results with exactly the input segment IDs and order."""
        ...


class BasicTranslationEngine:
    """Preserve the existing linear strategy behind the engine contract."""

    revision = "basic-v1"

    def __init__(
        self,
        executor: BatchExecutor,
        *,
        translator_id: str = "basic",
        revision: str = revision,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.executor = executor
        self.translator_id = translator_id
        self.revision = revision
        self.sleep = sleep

    def translate(
        self,
        document: XhtmlDocument,
        options: TranslationOptions,
        *,
        context: TranslationContext | None = None,
    ) -> TranslationResult:
        """Translate non-empty blocks and preserve all document structure."""
        runtime = context or TranslationContext()
        candidates = [block for block in document.blocks if block.text.strip()]
        batch_size, max_attempts = self._limits(options)
        if not candidates:
            return TranslationResult(
                document,
                TranslationMetrics(self.translator_id, self.revision),
            )

        translated = document
        batches = 0
        for start in range(0, len(candidates), batch_size):
            self._check_cancel(runtime)
            batch = tuple(candidates[start : start + batch_size])
            requests = tuple(self._request(block, options) for block in batch)
            results = self._execute_with_retry(requests, options, runtime, max_attempts)
            replacements = self._validate_and_map(batch, results)
            translated = translated.with_blocks(
                [
                    replacements.get(block.block_id, block)
                    for block in translated.blocks
                ]
            )
            batches += 1
            if runtime.on_batch_committed is not None:
                runtime.on_batch_committed(tuple(replacements))
            if runtime.on_progress is not None:
                runtime.on_progress(start + len(batch), len(candidates))

        self._check_cancel(runtime)
        return TranslationResult(
            translated,
            TranslationMetrics(
                translator_id=self.translator_id,
                translator_revision=self.revision,
                batches=batches,
                segments=len(candidates),
            ),
        )

    @staticmethod
    def _request(block: XhtmlBlock, options: TranslationOptions) -> SegmentRequest:
        """Expose block identity and markup to the executor."""
        return SegmentRequest(
            segment_id=block.block_id,
            text=block.text,
            source_language=options.source_language,
            target_language=options.target_language,
            markup=block.markup or None,
            attributes={"target_variant": options.target_variant},
        )

    def _execute_with_retry(
        self,
        requests: Sequence[SegmentRequest],
        options: TranslationOptions,
        context: TranslationContext,
        max_attempts: int,
    ) -> tuple[SegmentResult, ...]:
        """Retry only explicitly retryable failures within a finite budget."""
        for attempt in range(max_attempts):
            self._check_cancel(context)
            try:
                results = self.executor.execute(requests, options, context=context)
                self._check_cancel(context)
                return tuple(results)
            except TranslationError as exc:
                if not exc.retryable or attempt + 1 >= max_attempts:
                    raise
                self._check_cancel(context)
                if self.sleep is not None:
                    self.sleep(0)
        raise AssertionError("bounded retry loop exhausted unexpectedly")

    @staticmethod
    def _validate_and_map(
        blocks: Sequence[XhtmlBlock],
        results: Sequence[SegmentResult],
    ) -> dict[str, XhtmlBlock]:
        """Validate executor output and map it back without losing inline markup."""
        requests = tuple(
            SegmentRequest(block.block_id, block.text, "", "")
            for block in blocks
        )
        try:
            validated = validate_segment_results(requests, results)
        except Exception as exc:
            raise TranslationError(
                "invalid_result",
                f"Basic executor returned invalid batch output: {exc}",
            ) from exc

        by_id = {block.block_id: block for block in blocks}
        replacements: dict[str, XhtmlBlock] = {}
        for result in validated:
            block = by_id[result.segment_id]
            if not isinstance(result.markup, (str, type(None))):
                raise TranslationError(
                    "invalid_markup",
                    f"Invalid markup for segment {result.segment_id}",
                )
            markup = (
                result.markup
                if result.markup is not None
                else translated_markup(block.markup, block.text, result.text)
            )
            replacements[result.segment_id] = block.translated(result.text, markup)
        return replacements

    @staticmethod
    def _limits(options: TranslationOptions) -> tuple[int, int]:
        """Read only positive finite basic-engine limits from job options."""
        values: Any = options.translator_options
        batch_size = values.get("batch_size", 64)
        max_attempts = values.get("max_attempts", 2)
        for name, value in (("batch_size", batch_size), ("max_attempts", max_attempts)):
            if type(value) is not int or value < 1:
                raise TranslationError(
                    "invalid_options",
                    f"{name} must be a positive integer",
                )
        return batch_size, max_attempts

    @staticmethod
    def _check_cancel(context: TranslationContext) -> None:
        """Check cancellation at every batch boundary and after execution."""
        event = context.cancel_event
        if event is not None and event.is_set():
            raise TranslationCancelled()
