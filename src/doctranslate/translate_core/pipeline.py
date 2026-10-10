"""Format-neutral translation orchestration."""

from dataclasses import dataclass
import html
import re
from typing import Sequence

from .adapters import TranslationBackend
from .contracts import XhtmlDocument


class TranslationContractError(ValueError):
    """Raised when a backend violates the XHTML translation contract."""


_MARKUP_TAG = re.compile(r"(<[^>]+>)")


def translated_markup(markup: str, source: str, translated: str) -> str:
    """Replace a single plain-text XHTML node while preserving its tags."""
    if not markup or source == translated:
        return markup
    parts = _MARKUP_TAG.split(markup)
    text_indices = [index for index, part in enumerate(parts)
                    if part and not _MARKUP_TAG.fullmatch(part)]
    matching = [index for index in text_indices
                if html.unescape(parts[index]) == source]
    if len(matching) != 1:
        raise TranslationContractError(
            "Plain backend output cannot be safely mapped to XHTML markup; "
            "use a backend that returns translated inline markup"
        )
    parts[matching[0]] = html.escape(translated, quote=False)
    return "".join(parts)


@dataclass(frozen=True)
class MarkupTranslation:
    """Structured backend result for XHTML containing multiple text nodes."""

    text: str
    markup: str


@dataclass(frozen=True)
class TranslationPipeline:
    """Translate XHTML blocks while leaving layout metadata in the document."""

    backend: TranslationBackend

    def translate(self, document: XhtmlDocument) -> XhtmlDocument:
        """Translate language-bearing blocks and preserve order and metadata."""
        candidates = [block for block in document.blocks if block.text.strip()]
        if not candidates:
            return document
        values = self.backend.translate(
            [block.text for block in candidates],
            source_language=document.metadata.source_language,
            target_language=document.metadata.target_language,
        )
        if len(values) != len(candidates):
            raise TranslationContractError(
                f"Backend {self.backend.name!r} returned {len(values)} values for "
                f"{len(candidates)} blocks"
            )
        replacements = {}
        for block, value in zip(candidates, values):
            if isinstance(value, MarkupTranslation):
                if not isinstance(value.text, str) or not isinstance(value.markup, str):
                    raise TranslationContractError(
                        f"Backend {self.backend.name!r} returned invalid structured markup "
                        f"for block {block.block_id}"
                    )
                translated, markup = value.text, value.markup
            elif isinstance(value, str):
                translated = value
                markup = translated_markup(block.markup, block.text, translated)
            else:
                raise TranslationContractError(
                    f"Backend {self.backend.name!r} returned non-string value for "
                    f"block {block.block_id}"
                )
            replacements[block.block_id] = block.translated(translated, markup)
        return document.with_blocks(
            [replacements.get(block.block_id, block) for block in document.blocks]
        )


class CallableBackend:
    """Adapt a simple callable to the TranslationBackend protocol."""

    name = "callable"

    def __init__(self, translate_fn):
        """Wrap a callable without coupling the core pipeline to an AI SDK."""
        self._translate_fn = translate_fn

    def translate(self, texts: Sequence[str], *, source_language: str, target_language: str):
        """Delegate ordered texts and language metadata unchanged."""
        return self._translate_fn(texts, source_language, target_language)
