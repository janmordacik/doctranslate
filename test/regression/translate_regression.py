"""Fast, isolated regression tests for doctranslate. Only --live uses a real model."""
import argparse
import contextlib
import hashlib
import html
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BODY_EN = (
    "The original plan was to translate a short book about ancient science. "
    "The translator discovered several errors and suggested changes to the text. "
    "The author accepted many of these suggestions and explained the remaining differences."
)
BODY_CS = (
    "Původním plánem bylo přeložit krátkou knihu o starověké vědě. Překladatel však "
    "při práci objevil několik různých chyb a navrhl také změny původního textu. "
    "Autor mnohé z těchto podnětů přijal, další pečlivě posoudil a vysvětlil zbývající "
    "rozdíly mezi oběma vydáními knihy."
)
CZECH = "Příliš žluťoučký kůň úpěl ďábelské ódy."
PAIRS = [
    (BODY_EN, BODY_CS),
    ("Contents", "Obsah"), ("Foreword", "Předmluva"),
    ("Origins", "Počátky"), ("Ancient science", "Starověká věda"),
    ("The next chapter", "Následující kapitola"), ("Conclusion", "Závěr"),
    ("Ordinary text, ", "Obyčejný text, "),
    ("important discovery", "důležitý objev"),
    (", ordinary text again.", ", opět obyčejný text."),
    ("Original block", "Přeložený blok"),
    ("Original row", "Přeložený řádek"),
    ("A short translation test", "Krátký test překladu"),
    ("The book describes ancient science.", "Kniha popisuje starověkou vědu."),
    ("Keep this first line.", "Zachovejte první řádek."),
    ("Keep this second line.", "Zachovejte druhý řádek."),
    ("An important discovery.", "Důležitý objev."),
    ("An important discovery ", "Důležitý objev "),
]


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fake_text(value):
    for original, translated in sorted(PAIRS, key=lambda pair: len(pair[0]), reverse=True):
        value = value.replace(original, translated)
    return value


def load_translator(path):
    spec = importlib.util.spec_from_file_location("doctranslate.translate_test_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    required = ("prepare_text_translation", "restore_text_translation", "fill_translation_cache",
                "recover_saved_response", "replace_page_contents")
    if any(not hasattr(module, name) for name in required):
        raise RuntimeError("Use the current doctranslate package with plain-text batch support.")
    module.IN_LANG, module.OUT_LANG = "en", "cs"
    module.NUM_CTX = 8192
    module.AUTO_CONTEXT = False
    module.TIMEOUT = 10
    module.UNLOAD_TIMEOUT = 3
    module.API_CHECK_TIMEOUT = 2
    module.START_SERVER_IF_NEEDED = False
    # Python binds TIMEOUT default arguments when importing the translator.
    # Pass the test timeout explicitly, including when --live changes it.
    original_request = module.OllamaClient.request
    def limited_request(self, path, payload=None, **kwargs):
        kwargs.setdefault("timeout", module.TIMEOUT)
        return original_request(self, path, payload, **kwargs)
    module.OllamaClient.request = limited_request
    return module


def bind_job(module, source, target):
    module.configure(source, target, "en", "cs")
    module.LAST_JOB_FILE = target.parent / "translate_job.json"
    module.DEFAULT_INPUT_PDF = module.INPUT_PDF
    module.DEFAULT_OUTPUT_PDF = module.OUTPUT_PDF
    module.DEFAULT_PLAN_FILE = module.PLAN_FILE


def source_fonts(module, page):
    for alias, font in (("srcroman", "tiro"), ("srcbold", "tibo"), ("srcitalic", "tiit")):
        page.insert_font(fontname=alias, fontbuffer=module.fitz.Font(font).buffer)


def make_fixture(module, target):
    """Three small pages; only PyMuPDF, no additional dependency."""
    fitz = module.fitz
    with fitz.open() as pdf:
        page = pdf.new_page(width=440, height=390)
        source_fonts(module, page)
        page.insert_text((40, 50), "Contents", fontname="srcbold", fontsize=20)
        entries = ["1. Origins " + ". " * 16 + "3",
                   "2. Ancient science " + ". " * 11 + "4",
                   "3. The next chapter " + ". " * 10 + "5",
                   "4. Conclusion " + ". " * 14 + "6"]
        for n, entry in enumerate(entries):
            page.insert_text((52 if n == 2 else 40, 94 + 15 * n), entry,
                             fontname="srcroman", fontsize=12)
        page.insert_text((400, 365), "1", fontname="srcroman", fontsize=9)
        page = pdf.new_page(width=440, height=390)
        source_fonts(module, page)
        page.insert_text((40, 50), "Foreword", fontname="srcbold", fontsize=20)
        page.draw_rect(fitz.Rect(32, 80, 410, 205), color=(0.5, 0.4, 0.2), fill=(0.99, 0.97, 0.88))
        spare = page.insert_textbox(fitz.Rect(40, 90, 400, 195), BODY_EN, fontname="srcroman", fontsize=11)
        expect(spare >= 0, "Source paragraph did not fit")
        spare, _ = page.insert_htmlbox(
            fitz.Rect(40, 213, 400, 239),
            "<span>Ordinary text, </span><i>important discovery</i><span>, ordinary text again.</span>",
            css="body {font-family:serif;font-size:12pt;}")
        expect(spare >= 0, "Source italic row did not fit")
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 24, 16), False)
        image.clear_with(100)
        image.set_rect(fitz.IRect(3, 3, 18, 12), (210, 100, 20))
        page.insert_image(fitz.Rect(270, 260, 390, 340), pixmap=image)
        page.draw_rect(fitz.Rect(35, 265, 160, 337), color=(0.2, 0.4, 0.6), width=2)
        page.insert_text((400, 365), "2", fontname="srcroman", fontsize=9)
        page = pdf.new_page(width=440, height=390)
        source_fonts(module, page)
        page.insert_text((40, 80), "3.1415926535 + 2 = 5.1415926535", fontname="srcroman", fontsize=12)
        page.insert_text((40, 120), ". " * 24, fontname="srcroman", fontsize=12)
        page.insert_text((400, 365), "3", fontname="srcroman", fontsize=9)
        pdf.save(target, deflate=True)


def small_blocks(count, structured=False):
    blocks = []
    for n in range(count):
        markup = f'<span id="s0">Original block {n}</span>'
        styles = {"s0": ("Times-Roman", 12, 4, 0)}
        if structured:
            markup += '<br><span id="s1">Original row ' + ". \t" * 12 + ' 27</span><span id="s2"> 12345</span>'
            styles.update(s1=("Times-Italic", 12, 6, 0), s2=("Times-Roman", 12, 4, 0))
        blocks.append({"markup": markup, "styles": styles, "breaks": int(structured)})
    return blocks


class FakeOllama:
    """A local fake native API; it never forwards requests to a real server."""
    def __init__(self, module, mode="healthy", bad_id=None):
        self.module, self.mode, self.bad_id = module, mode, bad_id
        self.requests, self.payloads, self.loaded, self.unloads = [], [], False, 0
        self.before_chat = None
        self.handler_errors = []
        self.release = threading.Event()

    def __enter__(self):
        fake = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, value):
                body = json.dumps(value, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                models = [{"name": fake.module.MODEL, "context_length": 8192,
                           "size": 100, "size_vram": 100}]
                self.reply({"models": models if self.path == "/api/tags" or fake.loaded else []})

            def do_POST(self):
                try:
                    payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    if self.path == "/api/show":
                        self.reply({"model_info": {"general.architecture": "fake", "fake.context_length": 8192}})
                        return
                    if self.path == "/api/generate":
                        fake.loaded = payload["keep_alive"] != 0
                        fake.unloads += int(not fake.loaded)
                        self.reply({"done": True})
                        return
                    expect(self.path == "/api/chat", "Unexpected fake API endpoint")
                    originals = json.loads(payload["messages"][0]["content"].split("\n\n", 1)[1])
                    expect(payload["think"] is False, "Thinking should be disabled")
                    for fragments in originals.values():
                        expect(isinstance(fragments, dict), "AI received HTML instead of text fragments")
                        for text in fragments.values():
                            expect("<span" not in text and "<br>" not in text, "Layout tags reached the AI")
                            expect(not fake.module.LITERAL_RUN.search(text), "Long leaders reached the AI")
                    fake.loaded = True
                    fake.requests.append(originals)
                    fake.payloads.append(payload)
                    if fake.before_chat:
                        fake.before_chat(originals, len(fake.requests))
                    if fake.mode == "stall":
                        self.send_response(200)
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self.wfile.flush()
                        fake.release.wait(5)
                        return
                    translated = {key: {sid: fake_text(text) for sid, text in parts.items()}
                                  for key, parts in originals.items()}
                    done, reason = True, "stop"
                    if fake.mode == "two_bad" and len(fake.requests) == 1:
                        keys = list(translated)
                        first, second = (20, 120) if len(keys) >= 121 else (1, len(keys) - 2)
                        translated[keys[first]] = "Text outside tagged spans"
                        translated[keys[second]].pop(next(iter(translated[keys[second]])))
                    if fake.mode == "sticky" and fake.bad_id in translated:
                        translated[fake.bad_id] = "Invalid old HTML value"
                    if fake.mode == "all_bad":
                        translated = {}
                    content = json.dumps(translated, ensure_ascii=False)
                    if fake.mode == "truncated" and len(fake.requests) == 1:
                        keys = list(translated)
                        content = json.dumps(dict(list(translated.items())[:-1]), ensure_ascii=False)[:-1]
                        content += ", " + json.dumps(keys[-1]) + ': {"s0":"unfinished'
                        done, reason = False, "length"
                    self.reply({"message": {"content": content}, "done": done, "done_reason": reason,
                                "prompt_eval_count": 1000, "eval_count": 500, "eval_duration": 1000000000})
                except Exception as exc:
                    fake.handler_errors.append(str(exc))
                    self.reply({"error": "Fake API assertion failed: " + str(exc)})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()
        self.module.OLLAMA_URL = f"http://127.0.0.1:{self.server.server_port}"
        return self

    def __exit__(self, *args):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
        if self.handler_errors and args[0] is None:
            raise AssertionError("; ".join(self.handler_errors))


def fill(module, fake, blocks, folder, cache=None, callback=None, context=8192):
    module.OUTPUT_PDF = folder / "translated.pdf"
    cache = {} if cache is None else cache
    client = module.OllamaClient()
    client.context = context
    try:
        module.fill_translation_cache([(0, blocks)], cache, folder / "translations.json",
                                      client, on_commit=callback)
    finally:
        client.close()
    expect(not fake.loaded, "Model remained loaded after closing the client")
    return cache


def check_pdf(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    original_hash = module.fingerprint(sample)
    with FakeOllama(module) as fake:
        module.main()
        expect(len(fake.requests) == 1, "The tiny PDF should fit in one fake request")
        expect(fake.unloads == 1 and not fake.loaded, "Model unload was not confirmed")
    with module.fitz.open(sample) as original, module.fitz.open(module.OUTPUT_PDF) as translated:
        expect(len(translated) == 3, "Page count changed")
        toc = translated[0].get_text().splitlines()
        expect(sum(bool(re.match(r"^[1-4]\.", row)) for row in toc) == 4,
               "Contents entries lost their individual lines")
        expect("Předmluva" in translated[1].get_text(), "Translated heading is missing")
        spans = [s for b in translated[1].get_text("dict")["blocks"] if b["type"] == 0
                 for line in b["lines"] for s in line["spans"]]
        expect(any("důležitý" in s["text"] and s["flags"] & 2 for s in spans), "Italic text lost its style")
        expect(any("Původním" in s["text"] and s["size"] < 11 for s in spans),
               "Longer translated paragraph did not shrink to fit")
        source_spans = [s for b in original[1].get_text("dict")["blocks"] if b["type"] == 0
                        for line in b["lines"] for s in line["spans"]]
        source_font = next(s["font"] for s in source_spans if "The original" in s["text"])
        expect(any("Původním" in s["text"] and module.font_key(s["font"]) == module.font_key(source_font)
                   for s in spans), "Available embedded original font was replaced")
        expect("Původním plánem" in " ".join(translated[1].get_text().split()), "Paragraph disappeared")
        image_a, image_b = original[1].get_image_info(hashes=True), translated[1].get_image_info(hashes=True)
        expect([(x["bbox"], x["digest"]) for x in image_a] == [(x["bbox"], x["digest"]) for x in image_b],
               "Image content or position changed")
        for rect in (module.fitz.Rect(270, 260, 390, 340), module.fitz.Rect(30, 260, 170, 345)):
            expect(original[1].get_pixmap(clip=rect).samples == translated[1].get_pixmap(clip=rect).samples,
                   "Image/vector pixels changed")
        expect(original[2].get_pixmap().samples == translated[2].get_pixmap().samples,
               "Numeric-only page was re-typeset")
    expect(module.fingerprint(sample) == original_hash, "Source PDF was modified")


def check_unknown_font(module, folder, sample):
    with module.fitz.open(sample) as source:
        blocks = module.extract_blocks(source, 1)
        cache = {}
        for block in blocks:
            for ident, (_, size, flags, color) in list(block["styles"].items()):
                block["styles"][ident] = ("A", size, flags, color)
            prepared = module.prepare_text_translation(block)
            values = {ident: fake_text(text) for ident, text in prepared[0].items()}
            cache[module.cache_key(block)] = module.restore_text_translation(values, block, prepared)
        with tempfile.TemporaryDirectory() as font_folder:
            fonts = module.FontResolver(font_folder)
            fonts.local = []
            fonts.system_default = lambda *args: None
            broken = Path(font_folder) / "broken.ttf"
            broken.write_bytes(b"not a font")
            fonts.load_local_font(broken)
            work, _ = module.process_page(source, 1, fonts, cache, page_blocks=blocks)
            try:
                expect("Předmluva" in work[0].get_text(), "Unknown font prevented PDF generation")
                for filename in fonts.faces.values():
                    font = module.fitz.Font(fontfile=str(Path(font_folder) / filename))
                    expect(module.covers(font, CZECH), "Fallback font does not cover Czech characters")
                    expect(font.is_serif, "Unknown font A should default to serif")
                work.save(folder / "font-fallback-cs.pdf", deflate=True)
            finally:
                work.close()


def check_partial(module, folder, sample):
    blocks = small_blocks(182)
    with FakeOllama(module, "two_bad") as fake:
        def verify_before_retry(originals, number):
            if number == 2:
                expect(len(read_json(folder / "translations.json")) == 180,
                       "Validated results were not saved before retry")
                expect(set(originals) == {"p000001_b0021", "p000001_b0121"}, "Good blocks were resent")
        fake.before_chat = verify_before_retry
        cache = fill(module, fake, blocks, folder, context=131072)
        expect([len(r) for r in fake.requests] == [182, 2], "Whole batch was unnecessarily repeated")
        expect(len(cache) == 182, "Validated blocks are missing")


def check_truncated(module, folder, sample):
    with FakeOllama(module, "truncated") as fake:
        cache = fill(module, fake, small_blocks(5), folder)
        expect([len(r) for r in fake.requests] == [5, 1], "Complete prefix blocks were discarded")
        expect(len(cache) == 5, "Truncated response recovery did not finish")


def check_interrupt(module, folder, sample):
    blocks, cache = small_blocks(8), {}
    with FakeOllama(module, "two_bad") as fake:
        def stop_after_checkpoint():
            if len(cache) == 6:
                expect(len(read_json(folder / "translations.json")) == 6, "Checkpoint not saved")
                raise KeyboardInterrupt()
        try:
            fill(module, fake, blocks, folder, cache, stop_after_checkpoint)
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("Cancellation was suppressed")
        expect(len(fake.requests) == 1, "Cancelled work continued translating")
        fake.mode = "healthy"
        cache = fill(module, fake, blocks, folder, read_json(folder / "translations.json"))
        expect([len(r) for r in fake.requests] == [8, 2], "Resume resent completed blocks")
        expect(len(cache) == 8 and fake.unloads == 2, "Resume/cache/unload failed")


def check_legacy(module, folder, sample):
    blocks = small_blocks(4, structured=True)
    module.OUTPUT_PDF = folder / "translated.pdf"
    originals = {f"p000001_b{n + 1:04d}": module.protect_literals(block["markup"])[0]
                 for n, block in enumerate(blocks)}
    translated = {ident: fake_text(markup) for ident, markup in originals.items()}
    translated["p000001_b0002"] = "Outside a span" + translated["p000001_b0002"]
    translated["p000001_b0004"] = translated["p000001_b0004"].replace("<br>", "")
    module.atomic_json(module.OUTPUT_PDF.with_suffix(".ollama-error.json"), {
        "request": {"model": module.MODEL, "messages": [{
            "content": 'Translate ONLY natural-language words and sentences from "en" to "cs".\n\n' + json.dumps(originals)}]},
        "response": {"message": {"content": json.dumps(translated)}}})
    with FakeOllama(module) as fake:
        cache = fill(module, fake, blocks, folder)
        expect(list(fake.requests[0]) == ["p000001_b0002", "p000001_b0004"],
               "Valid legacy blocks were not recovered or invalid layout was accepted")
        expect(len(fake.requests) == 1 and len(cache) == 4, "Legacy recovery failed")


def check_reject_invalid(module, folder, sample):
    with FakeOllama(module, "all_bad") as fake:
        try:
            fill(module, fake, small_blocks(1), folder)
        except RuntimeError as exc:
            expect("failed after retries" in str(exc), "Failure did not identify the unresolved block")
        else:
            raise AssertionError("Invalid translation was silently accepted")
        expect(len(fake.requests) == 2, "Retries were not bounded")


def check_pdf_resume(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    with FakeOllama(module, "sticky", "p000002_b0001") as fake:
        def verify_checkpoint(originals, number):
            if number > 1:
                expect(read_json(module.PLAN_FILE)["html_last_saved"] == 1, "Ready HTML page was not saved before retry")
                expect(module.HTML_FILE.exists(), "No HTML exists before retry")
                expect(not module.OUTPUT_PDF.exists(), "The HTML phase unexpectedly typeset a PDF")
                doc = module.read_translation_html(module.HTML_FILE)
                expect(doc.blocks["p000001_b0001"]["status"] == "translated", "Valid HTML block was not committed")
        fake.before_chat = verify_checkpoint
        try:
            module.main()
        except RuntimeError:
            pass
        else:
            raise AssertionError("Persistent bad block was accepted")
        expect(not fake.loaded, "Model was not unloaded on failure")
        expect(read_json(module.PLAN_FILE)["html_last_saved"] == 1, "Unexpected HTML checkpoint")
        first_requests = len(fake.requests)
        fake.mode, fake.before_chat = "healthy", None
        module.entrypoint(["-outfile", str(module.OUTPUT_PDF)])
        expect(len(fake.requests) == first_requests + 1 and len(fake.requests[-1]) == 1,
               "Job resume resent translated blocks")
        expect(read_json(module.PLAN_FILE)["last_saved"] == 3 and not fake.loaded, "Resume did not finish")
        with module.fitz.open(module.OUTPUT_PDF) as pdf:
            expect("Obsah" in pdf[0].get_text() and "Předmluva" in pdf[1].get_text(), "Resumed PDF has missing pages")


def check_literals(module, folder, sample):
    block = small_blocks(1, structured=True)[0]
    prepared = module.prepare_text_translation(block)
    expect("s2" not in prepared[0], "Numeric-only fragment would be sent to AI")
    good = {ident: fake_text(text) for ident, text in prepared[0].items()}
    value = module.restore_text_translation(good, block, prepared)
    module.parse_translation(value, block["styles"], block["breaks"], block["markup"])
    expect(". \t" * 12 in value, "Literal leader spacing changed")
    marker = next(iter(prepared[2]))
    # First marker belongs to the language row; its loss must reject the block.
    bad = {ident: text.replace(marker, "") for ident, text in good.items()}
    try:
        module.restore_text_translation(bad, block, prepared)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing literal marker was accepted")
    bad = dict(good)
    bad["s0"] += "<br>"
    try:
        module.restore_text_translation(bad, block, prepared)
    except ValueError:
        pass
    else:
        raise AssertionError("Generated layout tag was accepted as plain text")


def check_timeout(module, folder, sample):
    # Exercise an actual HTTP read that stalls after headers, with no real model.
    module.TIMEOUT = 0.2
    module.OUTPUT_PDF = folder / "translated.pdf"
    with FakeOllama(module, "stall") as fake:
        client, started = module.OllamaClient(), time.monotonic()
        try:
            try:
                module.translate_batch([("p000001_b0001", small_blocks(1)[0])], client)
            except (TimeoutError, OSError):
                expect(time.monotonic() - started < 2, "The configured timeout did not stop the HTTP read")
            else:
                raise AssertionError("A stalled API response was accepted")
        finally:
            fake.release.set()
            client.close()
        expect(not fake.loaded and len(fake.requests) == 1, "Timeout repeated the request or skipped unload")


def check_cli(module, folder, sample):
    calls = []
    module.main = lambda: calls.append("main")
    module.open_gui = lambda args: calls.append("legacy-gui")
    module.discover_work_plan = lambda outfile=None: None

    # The current contract opens the queue GUI immediately without arguments.
    # Patch the lazy import so this check stays headless for every invocation.
    import types
    queue_module = types.SimpleNamespace(gui_main=lambda: calls.append("gui"))

    def call_queue_gui():
        previous_queue = sys.modules.get("doctranslate.queue_app")
        sys.modules["doctranslate.queue_app"] = queue_module
        try:
            module.entrypoint([])
        finally:
            if previous_queue is None:
                sys.modules.pop("doctranslate.queue_app", None)
            else:
                sys.modules["doctranslate.queue_app"] = previous_queue

    call_queue_gui()
    expect(calls == ["gui"], "No-argument launch did not choose queue GUI")
    target = folder / "CLI Český název.pdf"
    module.entrypoint(["-infile", str(sample), "-outfile", str(target), "-inlang", "English", "-outlang", "čeština"])
    expect(calls == ["gui", "main"] and (module.IN_LANG, module.OUT_LANG) == ("en", "cs"),
           "Explicit CLI parameters launched GUI or did not select languages")
    bind_job(module, sample, target)
    module.save_work_plan({"schema": module.SCHEMA, "source_hash": module.fingerprint(sample),
                          "model": module.MODEL, "first_page": 1, "last_page": 3,
                          "inlang": "en", "outlang": "cs"}, 0)
    module.discover_work_plan = lambda outfile=None: module.PLAN_FILE
    call_queue_gui()
    expect(calls == ["gui", "main", "gui"], "No-argument launch did not remain in queue GUI mode")

def forbid_ollama(module):
    def forbidden(*args, **kwargs):
        raise AssertionError("The offline phase attempted to create an Ollama client")
    module.OllamaClient = forbidden


def check_editable_html(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    module.configure_phases("html")
    with FakeOllama(module) as fake:
        module.main()
        expect(len(fake.requests) == 1 and fake.unloads == 1, "HTML phase did not use/unload one fake request")
    expect(not module.OUTPUT_PDF.exists(), "HTML-only phase generated a PDF")
    text = module.HTML_FILE.read_text(encoding="utf-8")
    expect('data:image/png;base64,' in text and '<figure data-page="2"' in text, "HTML is missing its image/page metadata")
    expect('<table' not in text and 'position:' not in text and 'font-family:' not in text,
           "Flow HTML unnecessarily imitates PDF layout")
    expect('data-block="p000001_b0001"' in text and 'data-span="s0"' in text, "Editable text markers are missing")
    document = module.read_translation_html(module.HTML_FILE)
    expect(document.metadata["complete"] and document.metadata["page_count"] == 3, "HTML metadata is incomplete")
    expect(all(b["status"] == "translated" for b in document.blocks.values()), "Some blocks remain pending")
    # Human correction is read from HTML, even with no translation cache.
    text = text.replace("Předmluva", "Úvod")
    module.HTML_FILE.write_text(text, encoding="utf-8")
    module.CACHE_FILE.unlink()
    forbid_ollama(module)
    module.NUM_CTX = 0  # The PDF phase must not depend on AI context configuration.
    module.entrypoint(["-phase", "pdf", "-htmlfile", str(module.HTML_FILE)])
    with module.fitz.open(module.OUTPUT_PDF) as pdf, module.fitz.open(sample) as original:
        expect("Úvod" in pdf[1].get_text() and "Předmluva" not in pdf[1].get_text(), "Manual correction was ignored")
        expect(original[1].get_pixmap(clip=module.fitz.Rect(270, 260, 390, 340)).samples ==
               pdf[1].get_pixmap(clip=module.fitz.Rect(270, 260, 390, 340)).samples, "Original image pixels changed")
    hash_a = module.fingerprint(module.OUTPUT_PDF)
    module.main()
    expect(module.fingerprint(module.OUTPUT_PDF) == hash_a, "Unchanged HTML unnecessarily regenerated the PDF")
    module.HTML_FILE.write_text(text.replace("Úvod", "Předmluva"), encoding="utf-8")
    module.main()
    with module.fitz.open(module.OUTPUT_PDF) as pdf:
        expect("Předmluva" in pdf[1].get_text(), "HTML update did not invalidate the completed PDF checkpoint")


def check_html_validation(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    with FakeOllama(module):
        module.main()
    text = module.HTML_FILE.read_text(encoding="utf-8")
    before = module.fingerprint(module.OUTPUT_PDF)
    plan_before = module.PLAN_FILE.read_bytes()
    metadata = module.read_translation_html(module.HTML_FILE).metadata
    bad_variants = [
        text.replace(metadata["source_hash"], "0" * 64),
        text.replace('data-span="s0"', 'data-span="unknown"', 1),
        text.replace('<br>', '', 1),
        text.replace('<span data-span="s0">', 'Stray text<span data-span="s0">', 1),
        re.sub(r'data-bbox="[^"]+"', 'data-bbox="[0, 0, 1, 1]"', text, count=1),
        text.replace('data-status="translated"', 'data-status="pending"', 1),
        re.sub(r'<(p|h3) id="p000001_b0001".*?</\1>', '', text, count=1, flags=re.S),
        text.replace('id="doctranslate-metadata"', 'id="missing-metadata"', 1),
    ]
    forbid_ollama(module)
    module.configure_phases("pdf")
    for index, bad in enumerate(bad_variants):
        expect(bad != text, f"Validation test {index} did not modify HTML")
        module.HTML_FILE.write_text(bad, encoding="utf-8")
        try:
            module.main()
        except RuntimeError as exc:
            expect("HTML" in str(exc), f"Unhelpful validation error: {exc}")
        else:
            raise AssertionError(f"Invalid HTML variant {index} was accepted")
        expect(module.fingerprint(module.OUTPUT_PDF) == before and module.PLAN_FILE.read_bytes() == plan_before,
               "Invalid HTML modified an existing PDF or checkpoint")
    module.HTML_FILE.write_text(text, encoding="utf-8")


def check_offline_pdf_resume(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    module.configure_phases("html")
    with FakeOllama(module):
        module.main()
    module.configure_phases("pdf")
    forbid_ollama(module)
    previous_save_mode = module.PDF_SAVE_MODE
    previous_checkpoint_pages = module.PDF_CHECKPOINT_PAGES
    module.PDF_SAVE_MODE = "checkpoint"
    module.PDF_CHECKPOINT_PAGES = 1
    original_save = module.save_pdf_atomic
    event = threading.Event()
    def stop_after_first(doc, path, compact=True):
        original_save(doc, path, compact=compact)
        event.set()
    module.save_pdf_atomic = stop_after_first
    try:
        module.main(event)
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("Cancellation during offline typesetting was ignored")
    expect(read_json(module.PLAN_FILE)["last_saved"] == 1, "PDF page checkpoint was not committed before cancellation")
    module.save_pdf_atomic = original_save
    module.entrypoint(["-outfile", str(module.OUTPUT_PDF)])
    expect(read_json(module.PLAN_FILE)["last_saved"] == 3, "Offline PDF resume did not finish")
    with module.fitz.open(module.OUTPUT_PDF) as pdf:
        expect("Obsah" in pdf[0].get_text() and "Předmluva" in pdf[1].get_text(), "Offline resume lost translated pages")
    module.PDF_SAVE_MODE = previous_save_mode
    module.PDF_CHECKPOINT_PAGES = previous_checkpoint_pages


def check_distinct_html_edits(module, folder, sample):
    # Two identical source blocks have one old cache key, but HTML edits belong
    # to specific occurrences. They must remain distinct when typesetting.
    source = folder / "duplicates-en.pdf"
    with module.fitz.open() as pdf:
        page = pdf.new_page(width=400, height=300)
        source_fonts(module, page)
        for y in (70, 140):
            page.insert_text((40, y), "Foreword", fontname="srcroman", fontsize=14)
        pdf.save(source)
    bind_job(module, source, folder / "duplicates-cs.pdf")
    module.configure_phases("html")
    with FakeOllama(module) as fake:
        module.main()
        expect(len(fake.requests) == 1 and len(fake.requests[0]) == 1, "Duplicate source translation was not reused")
    text = module.HTML_FILE.read_text(encoding="utf-8")
    expect(text.count("Předmluva") == 2, "HTML does not contain both source occurrences")
    text = text.replace("Předmluva", "První úvod", 1).replace("Předmluva", "Druhý úvod", 1)
    module.HTML_FILE.write_text(text, encoding="utf-8")
    # HTML resume must keep distinct manual edits, without calling AI again.
    original_request = module.OllamaClient.request
    module.OllamaClient.request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("Cached HTML caused a network request"))
    module.main()
    expect("První úvod" in module.HTML_FILE.read_text(encoding="utf-8") and
           "Druhý úvod" in module.HTML_FILE.read_text(encoding="utf-8"),
           "HTML resume overwrote per-occurrence edits")
    module.OllamaClient.request = original_request
    forbid_ollama(module)
    module.configure_phases("pdf")
    module.main()
    with module.fitz.open(module.OUTPUT_PDF) as pdf:
        text = pdf[0].get_text()
        expect("První úvod" in text and "Druhý úvod" in text, "Duplicate blocks received the same edited translation")


def check_legacy_job_html(module, folder, sample):
    bind_job(module, sample, folder / "translated.pdf")
    with FakeOllama(module):
        module.main()
    plan = read_json(module.PLAN_FILE)
    for key in ("html_file", "html_complete", "html_last_saved", "phase", "pdf_html_hash"):
        plan.pop(key, None)
    plan["layout_revision"] = 0
    module.atomic_json(module.PLAN_FILE, plan)
    module.HTML_FILE.unlink()
    module.OllamaClient.request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("Legacy cached job caused a network request"))
    module.entrypoint(["-outfile", str(module.OUTPUT_PDF)])
    expect(module.HTML_FILE.exists() and read_json(module.PLAN_FILE)["html_complete"], "Legacy job did not gain complete HTML")
    expect(read_json(module.PLAN_FILE)["last_saved"] == 3 and read_json(module.PLAN_FILE)["pdf_html_hash"],
           "Legacy PDF did not migrate to the two-phase checkpoint")


CHECKS = [
    ("PDF layout, shrinking, italics, hard breaks, images and numeric page", "layout", check_pdf),
    ("Unknown font A and corrupt font file, without system fonts", "font-fallback", check_unknown_font),
    ("182 blocks: save 180, retry only two invalid blocks", "partial", check_partial),
    ("Truncated JSON: keep complete blocks, retry unfinished one", "truncated", check_truncated),
    ("Interruption after checkpoint and cache-only resume", "interrupt", check_interrupt),
    ("Previous HTML response: salvage good blocks, reject two reported errors", "legacy", check_legacy),
    ("Persistent invalid response: bounded retries and explicit failure", "reject", check_reject_invalid),
    ("HTML checkpoint before retry and job JSON resume", "resume", check_pdf_resume),
    ("Protected literal spacing, numeric fragments and local layout", "literals", check_literals),
    ("Stalled HTTP response: enforce timeout and unload", "timeout", check_timeout),
    ("CLI languages, automatic GUI selection and job resume", "cli", check_cli),
    ("HTML-only phase, embedded image, human edit and offline PDF rebuild", "editable-html", check_editable_html),
    ("Eight invalid HTML variants: preserve PDF and checkpoint", "html-validation", check_html_validation),
    ("Offline PDF cancellation and job JSON resume, without AI", "offline-resume", check_offline_pdf_resume),
    ("Identical source blocks: preserve distinct per-occurrence HTML edits", "distinct-edits", check_distinct_html_edits),
    ("Legacy complete job: generate HTML and rebuild PDF from cache, without AI", "legacy-job", check_legacy_job_html),
]


def live_check(script, folder):
    module = load_translator(script)
    module.TIMEOUT, module.MAX_TOKENS = 120, 512
    module.UNLOAD_TIMEOUT = 20
    folder.mkdir()
    source = folder / "live-en.pdf"
    with module.fitz.open() as pdf:
        page = pdf.new_page(width=420, height=330)
        source_fonts(module, page)
        for text, y, font in [("A short translation test", 50, "srcbold"),
                              ("The book describes ancient science.", 95, "srcroman"),
                              ("Keep this first line.\nKeep this second line.", 140, "srcroman"),
                              ("An important discovery " + ". " * 16 + "7", 205, "srcitalic")]:
            page.insert_text((40, y), text, fontname=font, fontsize=12)
        page.insert_text((380, 305), "1", fontsize=9)
        pdf.save(source, deflate=True)
    bind_job(module, source, folder / "live-cs.pdf")
    client, cache = module.OllamaClient(), {}
    started, attempted = time.monotonic(), False
    try:
        client.ensure_available()
        client.tune_context()  # AUTO_CONTEXT=False: metadata only, no load/window probes.
        with module.fitz.open(source) as pdf:
            blocks = module.extract_blocks(pdf, 0)
            items = []
            for n, block in enumerate(blocks):
                if module.prepare_text_translation(block)[0]:
                    items.append((f"p000001_b{n + 1:04d}", block))
                else:
                    cache[module.cache_key(block)] = block["markup"]
            chars = len(json.dumps({ident: module.prepare_text_translation(block)[0]
                                   for ident, block in items}, ensure_ascii=False))
            expect(len(items) <= 4 and chars <= 1500, "Live input unexpectedly exceeds the short test budget")
            print(f"Live model: {module.MODEL}; {len(items)} short blocks, {chars} JSON characters.", flush=True)
            print("One inference request; context at most 8192, output at most 512 tokens, timeout 120 s.", flush=True)
            attempted = True
            try:
                translated = module.translate_batch(items, client)
            except module.PartialBatchTranslation as exc:
                for ident, block in items:
                    if ident in exc.translations:
                        cache[module.cache_key(block)] = exc.translations[ident]
                module.atomic_json(module.CACHE_FILE, cache)
                raise
            for ident, block in items:
                cache[module.cache_key(block)] = translated[ident]
            module.atomic_json(module.CACHE_FILE, cache)
            expect(any(translated[ident] != block["markup"] for ident, block in items),
                   "Model returned every English fragment unchanged")
            with tempfile.TemporaryDirectory() as fonts:
                work, _ = module.process_page(pdf, 0, module.FontResolver(fonts), cache, page_blocks=blocks)
                try:
                    work.save(module.OUTPUT_PDF, deflate=True)
                    text = work[0].get_text(sort=True)
                    expect("1" in text and text.strip(), "Output PDF is empty or lost the numeric footer")
                    preview = "\n".join(line.strip() for line in text.splitlines() if line.strip())
                    print("Model output for visual/language review:\n" + preview, flush=True)
                finally:
                    work.close()
        return {"passed": True, "model": module.MODEL, "context": client.context,
                "blocks": len(items), "input_json_characters": chars,
                "inference_requests": 1, "max_output_tokens": 512}
    finally:
        client.close()
        module.atomic_json(folder / "budget.json", {
            "model": module.MODEL, "context": client.context, "max_output_tokens": 512,
            "inference_requests": int(attempted), "request_timeout_seconds": 120,
            "elapsed_seconds": round(time.monotonic() - started, 3)})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fast PDF translator checks. Default: no real Ollama model or GPU.")
    parser.add_argument("--script", type=Path, default=Path(__file__).resolve().parents[2] / "src" / "doctranslate" / "translate.py",
                        help="translator module to test (default: src/doctranslate/translate.py)")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parents[2] / "tmp" / "doctranslate-test-results",
                        help="isolated folder for reports/PDFs; each run gets a new subfolder")
    parser.add_argument("--live", action="store_true", help="also run one short real Ollama request (120 s timeout)")
    args = parser.parse_args(argv)
    script = args.script.expanduser().resolve()
    if not script.is_file():
        parser.error(f"Translator not found: {script}. Use src/doctranslate/translate.py or --script.")
    root = args.outdir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=time.strftime("run-%Y%m%d-%H%M%S-"), dir=root))
    module = load_translator(script)
    sample = run / "sample-en.pdf"
    make_fixture(module, sample)
    print(f"Translator: {script}\nOffline checks: local fake API, no real model/GPU.\nResults: {run}", flush=True)
    report = {"script": str(script), "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
              "real_model_requested": args.live, "offline": [], "live": None}
    start = time.monotonic()
    for title, slug, check in CHECKS:
        folder = run / slug
        folder.mkdir()
        log, began = io.StringIO(), time.monotonic()
        error = None
        try:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                check(load_translator(script), folder, sample)
        except Exception as exc:
            import traceback
            error = str(exc)
            traceback.print_exc(file=log)
        (folder / "test.log").write_text(log.getvalue(), encoding="utf-8")
        elapsed = time.monotonic() - began
        report["offline"].append({"name": slug, "passed": error is None,
                                  "elapsed_seconds": round(elapsed, 3), "error": error})
        print(f"{'PASS' if error is None else 'FAIL'}  {title} ({elapsed:.2f}s)", flush=True)
        if error:
            print(log.getvalue(), flush=True)
    passed = sum(item["passed"] for item in report["offline"])
    failed = len(CHECKS) - passed
    print(f"Offline result: {passed} passed, {failed} failed in {time.monotonic() - start:.2f}s.", flush=True)
    if not failed and args.live:
        try:
            report["live"] = live_check(script, run / "live")
            print("PASS  Short real Ollama request and PDF generation", flush=True)
        except Exception as exc:
            failed += 1
            report["live"] = {"passed": False, "error": str(exc)}
            print(f"FAIL  Short real Ollama check: {exc}", flush=True)
    elif not args.live:
        print("Real model skipped. The --live option runs the short real-model check.", flush=True)
    else:
        print("Real model skipped because offline checks failed.", flush=True)
    module.atomic_json(run / "report.json", report)
    print(f"Report: {run / 'report.json'}", flush=True)
    return int(failed > 0)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted. Any active real-model request was cancelled and cleanup was attempted.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

