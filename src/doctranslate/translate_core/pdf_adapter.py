"""PDF plugin boundary.

The input adapter extracts text and layout metadata. The existing high-fidelity
PyMuPDF typesetter remains in translate.py until the migration is complete; callers
can inject it into PdfOutputAdapter without coupling the core to PDF.
"""

from html import escape
import hashlib
import os
from pathlib import Path
from typing import Callable

from .contracts import ResourceReference, SourceMetadata, XhtmlBlock, XhtmlDocument


class PdfResourceError(RuntimeError):
    """The source template resource cannot safely be used for rendering."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_source_resource(document: XhtmlDocument, base_path: Path | None = None) -> Path:
    """Resolve and verify the immutable PDF template referenced by XHTML."""
    resources = [item for item in document.metadata.resources if item.role == "source-template"]
    if not resources:
        raise PdfResourceError("XHTML document has no source-template PDF resource")
    resource = resources[0]
    candidate = Path(resource.path).expanduser()
    if not candidate.is_absolute():
        candidate = (base_path or Path.cwd()) / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise PdfResourceError(f"PDF source template does not exist: {candidate}")
    expected = resource.sha256 or document.metadata.source_sha256
    if expected and _sha256(candidate) != expected:
        raise PdfResourceError(f"PDF source template hash mismatch: {candidate}")
    return candidate


class PdfInputAdapter:
    """Extract a PDF into the format-neutral XHTML document contract."""

    media_type = "application/pdf"

    def read(self, source: Path) -> XhtmlDocument:
        """Extract ordered text blocks and bounding boxes from source."""
        try:
            import pymupdf as fitz
        except ImportError as exc:
            raise RuntimeError("PDF support requires pymupdf; install it separately") from exc

        source = Path(source).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        blocks: list[XhtmlBlock] = []
        page_layouts: list[dict[str, object]] = []
        with fitz.open(str(source)) as pdf:
            for page_index, page in enumerate(pdf):
                page_layouts.append({
                    "number": page_index + 1,
                    "width": float(page.rect.width),
                    "height": float(page.rect.height),
                    "rotation": int(page.rotation),
                })
                for order, raw in enumerate(page.get_text("blocks")):
                    x0, y0, x1, y1, text = raw[:5]
                    text = str(text).rstrip("\n")
                    block_id = f"p{page_index + 1:06d}_b{order + 1:04d}"
                    blocks.append(
                        XhtmlBlock(
                            block_id=block_id,
                            page_number=page_index + 1,
                            order=order,
                            text=text,
                            markup=f'<div data-block-id="{block_id}">{escape(text)}</div>',
                            bbox=(float(x0), float(y0), float(x1), float(y1)),
                        )
                    )
            pdf_metadata = dict(pdf.metadata or {})
            page_count = len(pdf)
        source_hash = _sha256(source)
        metadata = SourceMetadata(
            source_path=str(source),
            media_type=self.media_type,
            source_language="und",
            target_language="und",
            page_count=page_count,
            title=pdf_metadata.get("title") or source.stem,
            source_sha256=source_hash,
            resources=(
                ResourceReference(
                    "source-template",
                    "source-template",
                    self.media_type,
                    str(source),
                    source_hash,
                ),
            ),
            attributes={"pdf_metadata": pdf_metadata, "page_layouts": page_layouts},
        )
        return XhtmlDocument(metadata=metadata, blocks=tuple(blocks))


class PdfOutputAdapter:
    """Injectable PDF renderer boundary for the format-neutral pipeline."""

    media_type = "application/pdf"

    def __init__(self, renderer: Callable[[XhtmlDocument, Path], Path | None] | None = None):
        self._renderer = renderer

    def configure(self, renderer: Callable[[XhtmlDocument, Path], Path | None]) -> None:
        """Install the high-fidelity renderer at the composition boundary."""
        self._renderer = renderer

    def write(self, document: XhtmlDocument, target: Path) -> Path:
        """Delegate rendering to the configured high-fidelity PDF plugin."""
        if self._renderer is None:
            raise RuntimeError("PDF renderer is unavailable; configure the PDF plugin at startup")
        target = Path(target).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not os.access(target, os.W_OK):
            raise PermissionError(f"PDF target is not writable: {target}")
        result = self._renderer(document, target)
        return target if result is None else Path(result)
