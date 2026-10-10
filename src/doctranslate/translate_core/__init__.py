"""Reusable document-translation contracts independent of PDF rendering."""

from .contracts import ResourceReference, SourceMetadata, XhtmlBlock, XhtmlDocument
from .adapters import (
    AdapterRegistry,
    DocumentInputAdapter,
    DocumentOutputAdapter,
    TranslationBackend,
)
from .pipeline import MarkupTranslation, TranslationPipeline, TranslationContractError
from .pdf_adapter import PdfInputAdapter, PdfOutputAdapter
from .xhtml_codec import XhtmlCodec, XhtmlCodecError, dump_document, load_document

__all__ = [
    "AdapterRegistry",
    "DocumentInputAdapter",
    "DocumentOutputAdapter",
    "MarkupTranslation",
    "ResourceReference",
    "PdfInputAdapter",
    "PdfOutputAdapter",
    "SourceMetadata",
    "TranslationBackend",
    "TranslationContractError",
    "TranslationPipeline",
    "XhtmlBlock",
    "XhtmlDocument",
    "XhtmlCodec",
    "XhtmlCodecError",
    "dump_document",
    "load_document",
]
