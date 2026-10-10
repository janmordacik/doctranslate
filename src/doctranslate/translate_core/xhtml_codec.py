"""Safe, portable XHTML interchange codec.

The codec deliberately stores the document metadata separately from provider
configuration.  The body is a readable XHTML representation; block IDs and
their order are the stable bridge used by translation and format adapters.
"""

from __future__ import annotations

import base64
from dataclasses import asdict
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any

from .contracts import ResourceReference, SourceMetadata, XhtmlBlock, XhtmlDocument


SCHEMA = 1
META_NAME = "doctranslate-metadata"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")


class XhtmlCodecError(ValueError):
    """Raised when an interchange document is unsafe or structurally invalid."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _encode_metadata(value: dict[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_metadata(value: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        decoded = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise XhtmlCodecError("Invalid encoded XHTML metadata") from exc
    if not isinstance(decoded, dict):
        raise XhtmlCodecError("XHTML metadata must be a JSON object")
    return decoded


def _jsonable_metadata(document: XhtmlDocument) -> dict[str, Any]:
    metadata = document.metadata
    return {
        "schema": document.schema,
        "source": {
            "path": metadata.source_path,
            "media_type": metadata.media_type,
            "source_language": metadata.source_language,
            "target_language": metadata.target_language,
            "page_count": metadata.page_count,
            "title": metadata.title,
            "layout_revision": metadata.layout_revision,
            "source_sha256": metadata.source_sha256,
            "attributes": dict(metadata.attributes),
            "resources": [asdict(item) for item in metadata.resources],
            "extensions": dict(metadata.extensions),
        },
    }


def _resource_list(value: Any) -> tuple[ResourceReference, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise XhtmlCodecError("XHTML resources must be a list")
    result = []
    for item in value:
        if not isinstance(item, dict):
            raise XhtmlCodecError("XHTML resource must be an object")
        try:
            result.append(
                ResourceReference(
                    resource_id=str(item["resource_id"]),
                    role=str(item["role"]),
                    media_type=str(item["media_type"]),
                    path=str(item["path"]),
                    sha256=item.get("sha256"),
                )
            )
        except KeyError as exc:
            raise XhtmlCodecError(f"XHTML resource is missing {exc.args[0]}") from exc
    return tuple(result)


def _metadata_from_json(value: dict[str, Any]) -> tuple[int, SourceMetadata]:
    schema = value.get("schema", SCHEMA)
    if not isinstance(schema, int) or schema > SCHEMA:
        raise XhtmlCodecError(f"Unsupported XHTML schema: {schema!r}")
    source = value.get("source")
    if not isinstance(source, dict):
        raise XhtmlCodecError("XHTML metadata has no source object")
    required = ("path", "media_type", "source_language", "target_language")
    if any(not isinstance(source.get(key), str) for key in required):
        raise XhtmlCodecError("XHTML source metadata is incomplete")
    metadata = SourceMetadata(
        source_path=source["path"],
        media_type=source["media_type"],
        source_language=source["source_language"],
        target_language=source["target_language"],
        page_count=source.get("page_count"),
        title=source.get("title"),
        layout_revision=int(source.get("layout_revision", 1)),
        attributes=source.get("attributes", {}),
        source_sha256=source.get("source_sha256"),
        resources=_resource_list(source.get("resources")),
        extensions=source.get("extensions", {}),
    )
    return schema, metadata


def _attrs_to_text(attrs: list[tuple[str, str | None]]) -> str:
    bits = []
    for name, value in attrs:
        bits.append(" " + name)
        if value is not None:
            bits.append('="' + html.escape(value, quote=True) + '"')
    return "".join(bits)


class _BlockParser(HTMLParser):
    """Parse only the small canonical subset and preserve inline markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.metadata: dict[str, Any] | None = None
        self.blocks: list[XhtmlBlock] = []
        self._active: dict[str, Any] | None = None
        self._depth = 0
        self._root_seen = False

    def _append(self, value: str) -> None:
        if self._active is not None:
            self._active["parts"].append(value)

    def handle_decl(self, decl: str) -> None:
        raise XhtmlCodecError("DOCTYPE and external declarations are not allowed")

    def handle_comment(self, data: str) -> None:
        self._append("<!--" + data + "-->")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_map = {name.lower(): value for name, value in attrs}
        if tag == "script" or tag == "iframe" or tag == "object":
            raise XhtmlCodecError(f"Unsupported active XHTML element: {tag}")
        if tag == "meta" and attrs_map.get("name") == META_NAME:
            self._root_seen = True
            self._active = self._active
        if tag == "div" and (
            attrs_map.get("data-block-id") or attrs_map.get("data-block")
        ):
            if self._active is not None:
                raise XhtmlCodecError("Nested translation blocks are not allowed")
            block_id = attrs_map.get("data-block-id") or attrs_map.get("data-block")
            if not block_id or not _SAFE_ID.fullmatch(block_id):
                raise XhtmlCodecError(f"Invalid XHTML block ID: {block_id!r}")
            try:
                page = int(attrs_map.get("data-page", "1"))
                order = int(attrs_map.get("data-order", str(len(self.blocks))))
            except ValueError as exc:
                raise XhtmlCodecError(f"Invalid page/order for block {block_id}") from exc
            bbox = None
            raw_bbox = attrs_map.get("data-bbox")
            if raw_bbox:
                try:
                    numbers = tuple(float(part) for part in raw_bbox.split(","))
                except ValueError as exc:
                    raise XhtmlCodecError(f"Invalid bbox for block {block_id}") from exc
                if len(numbers) != 4:
                    raise XhtmlCodecError(f"Invalid bbox for block {block_id}")
                bbox = numbers
            self._active = {
                "id": block_id,
                "page": page,
                "order": order,
                "bbox": bbox,
                "style": attrs_map.get("data-style"),
                "parts": [],
                "text": [],
            }
            self._depth = 1
            return
        if self._active is not None:
            self._append("<" + tag + _attrs_to_text(attrs) + ">")
            self._depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self._active is not None:
            self._append("<" + tag + _attrs_to_text(attrs) + "/>")
        if tag == "meta":
            attrs_map = {name.lower(): value for name, value in attrs}
            if attrs_map.get("name") == META_NAME and attrs_map.get("content"):
                self.metadata = _decode_metadata(attrs_map["content"] or "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._active is None:
            return
        if tag == "div" and self._depth == 1:
            active = self._active
            markup = "".join(active["parts"])
            self.blocks.append(
                XhtmlBlock(
                    block_id=active["id"],
                    page_number=active["page"],
                    order=active["order"],
                    text="".join(active["text"]),
                    markup=markup,
                    bbox=active["bbox"],
                    style={} if not active["style"] else {"raw": active["style"]},
                )
            )
            self._active = None
            self._depth = 0
            return
        self._append("</" + tag + ">")
        self._depth = max(1, self._depth - 1)

    def handle_data(self, data: str) -> None:
        self._append(html.escape(data, quote=False))
        if self._active is not None:
            self._active["text"].append(data)

    def handle_entityref(self, name: str) -> None:
        self._append("&" + name + ";")
        if self._active is not None:
            self._active["text"].append(html.unescape("&" + name + ";"))

    def handle_charref(self, name: str) -> None:
        self._append("&#" + name + ";")
        if self._active is not None:
            self._active["text"].append(html.unescape("&#" + name + ";"))


def _block_element(block: XhtmlBlock) -> str:
    attrs = [
        ("class", "doctranslate-block"),
        ("data-block-id", block.block_id),
        ("data-page", str(block.page_number)),
        ("data-order", str(block.order)),
    ]
    if block.bbox is not None:
        attrs.append(("data-bbox", ",".join(str(value) for value in block.bbox)))
    if block.style.get("raw"):
        attrs.append(("data-style", str(block.style["raw"])))
    attr_text = "".join(
        " " + name + '="' + html.escape(value, quote=True) + '"' for name, value in attrs
    )
    inner = block.markup or html.escape(block.text, quote=False)
    return "<div" + attr_text + ">" + inner + "</div>"


def dump_document(document: XhtmlDocument, path: Path) -> Path:
    """Atomically serialize a validated document into editable XHTML."""
    if document.schema > SCHEMA:
        raise XhtmlCodecError(f"Unsupported XHTML schema: {document.schema}")
    ids = [block.block_id for block in document.blocks]
    if any(not _SAFE_ID.fullmatch(block_id) for block_id in ids):
        raise XhtmlCodecError("XHTML block IDs must be stable safe identifiers")
    if len(ids) != len(set(ids)):
        raise XhtmlCodecError("XHTML block identifiers must be unique")
    metadata = _encode_metadata(_jsonable_metadata(document))
    body = "\n".join(_block_element(block) for block in document.blocks)
    rendered = (
        '<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml"><head>\n'
        '<meta charset="utf-8"/>\n<meta name="' + META_NAME + '" content="' + metadata + '"/>\n'
        "<title>" + html.escape(document.metadata.title or "Translation") + "</title>\n"
        "</head><body>\n" + body + "\n</body></html>\n"
    )
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(target)
    return target


def load_document(path: Path) -> XhtmlDocument:
    """Load canonical XHTML or a constrained legacy block representation."""
    source = Path(path).expanduser().resolve()
    try:
        text = source.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise XhtmlCodecError(f"Cannot read XHTML {source}: {exc}") from exc
    if "<!DOCTYPE" in text.upper():
        # A doctype in a normal HTML file is not an external entity by itself,
        # but rejecting declarations keeps the parser contract deterministic.
        text = re.sub(r"<!DOCTYPE\s+html\s*>", "", text, flags=re.IGNORECASE)
    parser = _BlockParser()
    try:
        parser.feed(text)
        parser.close()
    except XhtmlCodecError:
        raise
    except Exception as exc:
        raise XhtmlCodecError(f"Invalid XHTML markup in {source}: {exc}") from exc
    if parser.metadata is None:
        raise XhtmlCodecError("XHTML metadata marker is missing")
    schema, metadata = _metadata_from_json(parser.metadata)
    if len({block.block_id for block in parser.blocks}) != len(parser.blocks):
        raise XhtmlCodecError("XHTML block identifiers must be unique")
    return XhtmlDocument(metadata=metadata, blocks=tuple(parser.blocks), schema=schema)


class XhtmlCodec:
    """Object facade used by composition roots and tests."""

    schema = SCHEMA

    def load(self, path: Path) -> XhtmlDocument:
        return load_document(path)

    def dump(self, document: XhtmlDocument, path: Path) -> Path:
        return dump_document(document, path)
