import io
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.config import ConfigError, get_language, get_workdir, save_config
from doctranslate.queue_app import (
    GUI_TEXT, FileLock, QueueConflictError, QueueStore, QueueGui,
    OllamaDiscovery, StorageError, WorkerController, atomic_write,
    discover_ollama_models, discover_translation_html, make_job, process_status,
)
from doctranslate.queue_worker import Worker
from doctranslate.queue_worker import JobOptions


class QueueStoreTests(unittest.TestCase):
    def test_worker_options_preserve_target_variant(self):
        options = JobOptions.from_job({
            "input": "in.pdf", "output": "out.pdf", "inlang": "en", "outlang": "cs",
            "phase": "html", "target_variant": "cs-expert",
        })
        self.assertEqual(options.target_variant, "cs-expert")

    def test_queue_validates_style_against_target_language(self):
        valid = make_job("valid.pdf", outlang="cs", target_variant="cs-expert")
        self.store.set_jobs([valid])
        loaded = self.store.jobs()[0]
        self.assertEqual(loaded["target_variant"], "cs-expert")
        self.assertTrue(loaded["style_revision"])

        invalid = make_job("invalid.pdf", outlang="de", target_variant="cs-expert")
        with self.assertRaises(ValueError):
            self.store.set_jobs([invalid])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue_path = Path(self.temp.name) / "queue.json"
        self.store = QueueStore(self.queue_path)

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_config_uses_fallback_and_locale_language(self):
        config = Path(self.temp.name) / "missing.json"
        fallback = Path(self.temp.name) / "fallback"
        self.assertEqual(get_workdir(config, fallback), fallback.resolve())
        self.assertIn(get_language(config), {"cs", "en"})

    def test_config_roundtrip_persists_workdir_and_language(self):
        config = Path(self.temp.name) / "translate.config.json"
        workdir = Path(self.temp.name) / "work"
        workdir.mkdir()
        save_config(workdir, config, language="en")
        self.assertEqual(get_workdir(config), workdir.resolve())
        self.assertEqual(get_language(config), "en")

    def test_discover_translation_html_matches_source_hash_and_completion(self):
        source = Path(self.temp.name) / "source – book.pdf"
        output = Path(self.temp.name) / "translated.pdf"
        html = Path(self.temp.name) / "translated – complete.html"
        source.write_bytes(b"source-pdf")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        metadata = {
            "format": "doctranslate-html",
            "complete": True,
            "source_hash": source_hash,
            "inlang": "en",
            "outlang": "cs",
        }
        html.write_text(
            '<script type="application/json" id="doctranslate-metadata">'
            + json.dumps(metadata)
            + "</script>",
            encoding="utf-8",
        )
        self.assertEqual(
            discover_translation_html(source, output, inlang="en", outlang="cs"),
            html.resolve(),
        )

    def test_discover_translation_html_ignores_incomplete_html(self):
        source = Path(self.temp.name) / "source.pdf"
        output = Path(self.temp.name) / "translated.pdf"
        html = Path(self.temp.name) / "translated.html"
        source.write_bytes(b"source-pdf")
        metadata = {
            "complete": False,
            "source_hash": hashlib.sha256(source.read_bytes()).hexdigest(),
            "inlang": "en",
            "outlang": "cs",
        }
        html.write_text(
            '<script id="doctranslate-metadata">'
            + json.dumps(metadata)
            + "</script>",
            encoding="utf-8",
        )
        self.assertIsNone(discover_translation_html(source, output))

    def test_job_can_carry_pdf_phase_and_html_path(self):
        html = Path(self.temp.name) / "translated.html"
        job = make_job("book.pdf", phase="pdf", html_file=html)
        self.assertEqual(job["phase"], "pdf")
        self.assertEqual(job["html_file"], str(html.resolve()))

    def test_malformed_config_is_not_silently_replaced_by_cwd(self):
        config = Path(self.temp.name) / "translate.config.json"
        config.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ConfigError):
            get_workdir(config)

    def test_valid_queue_backup_is_used_and_announced(self):
        self.store.set_jobs([make_job("book.pdf")])
        backup = self.queue_path.with_suffix(".bak")
        backup.write_bytes(self.queue_path.read_bytes())
        self.queue_path.write_text("{broken", encoding="utf-8")
        with patch("sys.stderr") as stderr:
            jobs = self.store.jobs()
        self.assertEqual(len(jobs), 1)
        stderr.write.assert_called()

    def test_worker_run_job_fake_backend_completes_offline(self):
        from doctranslate import translate

        job = make_job("book.pdf", model="fake:1b")
        self.store.set_jobs([job])
        worker = Worker(self.queue_path)
        with patch.object(translate, "configure"), \
             patch.object(translate, "configure_phases"), \
             patch.object(translate, "main", return_value=None):
            worker.run_job(job)
        self.assertEqual(self.store.jobs()[0]["state"], "done")
        self.assertIsNone(worker.current_job_id)
        events = self.queue_path.with_name("queue.events.log").read_text(encoding="utf-8")
        self.assertIn('"event": "worker.job.started"', events)
        self.assertIn('"event": "worker.job.completed"', events)

    def test_worker_preview_is_written_to_runtime_state_only(self):
        worker = Worker(self.queue_path)
        worker.current_job_id = "job-preview"
        worker.runtime_state = "in_progress"
        worker.publish_preview({
            "block_id": "p000002_b0003",
            "page": 2,
            "stage": "translated",
            "source_text": "Hello",
            "translated_text": "Ahoj",
        })

        state = json.loads(
            self.queue_path.with_name("worker-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(state["job_id"], "job-preview")
        self.assertEqual(state["preview"]["translated_text"], "Ahoj")
        # Preview patří pouze do runtime sidecaru, nesmí vytvořit ani změnit
        # perzistentní frontu.
        self.assertFalse(self.queue_path.exists())

    def test_worker_preview_is_throttled_but_terminal_update_is_immediate(self):
        worker = Worker(self.queue_path)
        worker.current_job_id = "job-preview"
        worker.runtime_state = "in_progress"
        preview = {"block_id": "p1_b1", "stage": "translating", "source_text": "A"}

        with patch("doctranslate.queue_worker.time.monotonic", side_effect=(100.0, 105.0, 109.0)):
            with patch.object(worker, "write_state") as write_state:
                worker.publish_preview(preview)
                worker.publish_preview({**preview, "block_id": "p1_b2", "source_text": "B"})
                worker.publish_preview({
                    **preview,
                    "block_id": "p1_b2",
                    "stage": "translated",
                    "translated_text": "B",
                })

        self.assertEqual(write_state.call_count, 2)
        self.assertEqual(worker.activity_fields["preview"]["stage"], "translated")

    def test_worker_does_not_leak_model_between_jobs(self):
        from doctranslate import translate

        first = make_job("first.pdf", model="model-a", first_page=2, last_page=4)
        second = make_job("second.pdf", model=None)
        self.store.set_jobs([first, second])
        worker = Worker(self.queue_path)
        seen = []

        def fake_main(_cancel_event):
            seen.append((translate.MODEL, translate.FIRST_PAGE, translate.LAST_PAGE))

        with patch.object(translate, "configure"), \
             patch.object(translate, "configure_phases"), \
             patch.object(translate, "main", side_effect=fake_main):
            worker.run_job(first)
            worker.run_job(second)
        self.assertEqual(seen, [("model-a", 2, 4), (translate.DEFAULT_MODEL, 1, None)])

    def test_gui_localization_contains_core_controls(self):
        required = {"start", "send", "stop", "new", "copy", "pause", "prepare", "delete", "refresh"}
        for language in ("cs", "en"):
            self.assertTrue(required.issubset(GUI_TEXT[language]))
            self.assertNotEqual(GUI_TEXT[language]["start"], GUI_TEXT[language]["send"])


    def test_gui_copy_selected_job_populates_editable_draft(self):
        class Var:
            def __init__(self, value=""):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        class Tree:
            def selection(self):
                return (source["id"],)

        source = make_job("source.pdf", "copy.pdf", model="translategemma:4b",
                          provider="ollama", profile="local", phase="pdf",
                          html_file="source.html", first_page=2, last_page=5)
        source.update({"inlang": "de", "outlang": "cs", "input_format": "pdf",
                       "output_format": "pdf"})
        fake = QueueGui.__new__(QueueGui)
        fake.form_editing = False
        fake.jobs_draft = [source]
        fake.tree = Tree()
        fake.input_var = Var()
        fake.output_var = Var()
        fake.html_file_var = Var()
        fake.provider_var = Var()
        fake.profile_var = Var()
        fake.model_var = Var()
        fake.auto_output_suggestion = None
        fake.auto_html_suggestion = None
        fake.editing_job_template = None
        fake._set_phase_value = lambda value: setattr(fake, "phase_value", value)
        fake._set_job_form_state = lambda editing: setattr(fake, "form_editing", editing)
        fake._refresh_provider_controls = lambda: None
        fake._log_action = lambda *_args, **_kwargs: None
        fake.render = lambda: None

        QueueGui.copy_selected_job(fake)

        self.assertEqual(fake.editing_job_template, source)
        self.assertEqual(fake.input_var.get(), source["input"])
        self.assertEqual(fake.output_var.get(), source["output"])
        self.assertEqual(fake.html_file_var.get(), source["html_file"])
        self.assertEqual(fake.phase_value, "pdf")
        self.assertEqual(fake.form_editing, True)

    def test_gui_double_click_on_row_uses_copy_action(self):
        class Tree:
            def __init__(self):
                self.current = "job-1"

            def identify_row(self, _y):
                return self.current

            def selection_set(self, item):
                self.current = item

            def focus(self, _item):
                pass

        fake = QueueGui.__new__(QueueGui)
        fake.form_editing = False
        fake.tree = Tree()
        fake.select_job = Mock()
        fake.copy_selected_job = Mock()

        result = QueueGui.copy_job_on_double_click(fake, type("Event", (), {"y": 10})())

        self.assertEqual(result, "break")
        fake.select_job.assert_called_once_with()
        fake.copy_selected_job.assert_called_once_with()

    def test_gui_copy_commit_creates_new_prepared_job_with_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "source.pdf"
            source_path.write_bytes(b"pdf")
            output_path = Path(folder) / "copy.pdf"
            source = make_job(source_path, output_path, model="model-a",
                              provider="ollama", profile="local", phase="pdf",
                              html_file=Path(folder) / "source.html",
                              first_page=2, last_page=5, inlang="de", outlang="cs",
                              input_format="pdf", output_format="pdf")
            source["state"] = "done"
            source["error"] = "old error"

            class Var:
                def __init__(self, value=""):
                    self.value = value

                def get(self):
                    return self.value

                def set(self, value):
                    self.value = value

            class Tree:
                def selection_set(self, _item):
                    pass

                def focus(self, _item):
                    pass

            fake = QueueGui.__new__(QueueGui)
            fake.form_editing = True
            fake.jobs_draft = [source]
            fake.editing_job_template = source
            fake.input_var = Var(str(source_path))
            fake.output_var = Var(str(output_path))
            fake.html_file_var = Var(str(Path(folder) / "source.html"))
            fake.phase_var = Var("pdf")
            fake.model_var = Var("model-a")
            fake.provider_var = Var("ollama")
            fake.profile_var = Var("local")
            fake.dirty = False
            fake.messagebox = type("MessageBox", (), {"showerror": lambda *_args: None})()
            fake._set_job_form_state = lambda editing: setattr(fake, "form_editing", editing)
            fake._log_action = lambda *_args, **_kwargs: None
            fake.render = lambda: None
            fake.tree = Tree()
            fake.select_job = lambda: None

            QueueGui.commit_job_form(fake)

            copied = fake.jobs_draft[-1]
            self.assertNotEqual(copied["id"], source["id"])
            self.assertEqual(copied["state"], "prepared")
            self.assertIsNone(copied["error"])
            for key in ("inlang", "outlang", "input_format", "output_format",
                        "first_page", "last_page", "model", "provider", "profile"):
                self.assertEqual(copied.get(key), source.get(key), key)

    def test_gui_phase_labels_are_format_neutral(self):
        for language in ("cs", "en"):
            self.assertEqual(GUI_TEXT[language]["phase_html"], "in -> html")
            self.assertEqual(GUI_TEXT[language]["phase_pdf"], "html -> out")
            self.assertEqual(GUI_TEXT[language]["phase_both"], "in -> html -> out")

    def test_gui_render_preserves_existing_job_selection(self):
        class FakeTree:
            def __init__(self, selected):
                self.items = []
                self.selected = [selected]
                self.focused = None

            def selection(self):
                return tuple(self.selected)

            def get_children(self):
                return tuple(self.items)

            def delete(self, item):
                self.items.remove(item)

            def insert(self, _parent, _position, iid, values):
                self.items.append(iid)

            def exists(self, item):
                return item in self.items

            def selection_set(self, item):
                self.selected = [item]

            def focus(self, item):
                self.focused = item

        class FakeLabel:
            def configure(self, **_kwargs):
                pass

        class FakeButton:
            def __init__(self):
                self.state = None

            def configure(self, **kwargs):
                self.state = kwargs.get("state", self.state)

        first = make_job("first.pdf")
        second = make_job("second.pdf")
        fake = type("Gui", (), {
            "tree": FakeTree(second["id"]),
            "jobs_draft": [first, second],
            "dirty": False,
            "labels": {"status": FakeLabel()},
            "buttons": {"stop": FakeButton()},
            "controller": type("Controller", (), {
                "running": lambda _self: False,
                "stopping": lambda _self: False,
            })(),
            "store": type("Store", (), {"load": lambda _self: {"revision": 3}})(),
            "_worker_activity_text": lambda _self, _state: "translating",
            "_t": lambda _self, key: key,
        })()

        QueueGui.render(fake)

        self.assertEqual(fake.tree.selection(), (second["id"],))
        self.assertEqual(fake.tree.focused, second["id"])
        self.assertEqual(fake.buttons["stop"].state, "normal")

    def test_gui_render_disables_stop_while_worker_is_stopping(self):
        class FakeTree:
            def selection(self):
                return ()

            def get_children(self):
                return ()

            def delete(self, _item):
                pass

            def insert(self, _parent, _position, iid, values):
                pass

            def exists(self, _item):
                return False

            def selection_set(self, _item):
                pass

            def focus(self, _item):
                pass

        class FakeButton:
            def __init__(self):
                self.state = None

            def configure(self, **kwargs):
                self.state = kwargs.get("state", self.state)

        button = FakeButton()
        fake = type("Gui", (), {
            "tree": FakeTree(),
            "jobs_draft": [],
            "dirty": False,
            "labels": {"status": type("Label", (), {
                "configure": lambda _self, **_kwargs: None,
            })()},
            "buttons": {"stop": button},
            "controller": type("Controller", (), {
                "running": lambda _self: True,
                "stopping": lambda _self: True,
            })(),
            "store": type("Store", (), {"load": lambda _self: {"revision": 3}})(),
            "_t": lambda _self, key: key,
        })()

        QueueGui.render(fake)

        self.assertEqual(button.state, "disabled")

    def test_gui_worker_activity_includes_progress(self):
        fake = type("Gui", (), {
            "_t": lambda _self, key: {
                "activity_translating": "translating with AI",
                "unit_pages": "pages",
            }.get(key, key),
            "phase_choices": ("both", "html", "pdf"),
            "_phase_display": lambda _self, phase: {
                "both": "in -> html -> out",
                "html": "in -> html",
                "pdf": "html -> out",
            }.get(str(phase or ""), str(phase or "")),
        })()
        detail = QueueGui._worker_activity_text(fake, {
            "activity": "translating",
            "phase": "html",
            "completed": 210,
            "total": 493,
            "progress": 210 / 493,
            "unit": "pages",
        })
        self.assertIn("210/493 pages", detail)
        self.assertIn("43 %", detail)

    def test_worker_report_progress_persists_runtime_snapshot(self):
        worker = Worker(self.queue_path)
        worker.current_job_id = "job-progress"
        worker.activity = "typesetting"
        worker.report_progress(7, 10, unit="pages", current_page=8)
        state = json.loads(worker.state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["completed"], 7)
        self.assertEqual(state["total"], 10)
        self.assertEqual(state["unit"], "pages")
        self.assertEqual(state["current_page"], 8)
        self.assertAlmostEqual(state["progress"], 0.7)

    def test_gui_render_updates_progress_bar_from_worker_state(self):
        class FakeTree:
            def selection(self):
                return ()

            def get_children(self):
                return ()

            def delete(self, _item):
                pass

            def insert(self, *_args, **_kwargs):
                pass

            def exists(self, _item):
                return False

            def selection_set(self, _item):
                pass

            def focus(self, _item):
                pass

        class FakeProgress:
            def __init__(self):
                self.value = None

            def configure(self, **kwargs):
                self.value = kwargs["value"]

        fake = type("Gui", (), {
            "tree": FakeTree(),
            "jobs_draft": [],
            "dirty": False,
            "progress": FakeProgress(),
            "labels": {"status": type("Label", (), {"configure": lambda _self, **_kwargs: None})()},
            "buttons": {"stop": type("Button", (), {"configure": lambda _self, **_kwargs: None})()},
            "controller": type("Controller", (), {
                "running": lambda _self: True,
                "stopping": lambda _self: False,
                "state_snapshot": lambda _self: {"progress": 0.42, "activity": "translating"},
            })(),
            "store": type("Store", (), {"load": lambda _self: {"revision": 3}})(),
            "_worker_activity_text": lambda _self, _state: "translating",
            "_t": lambda _self, key: key,
        })()
        QueueGui.render(fake)
        self.assertEqual(fake.progress.value, 42)

    def test_queue_cancel_stop_clears_pending_request(self):
        self.store.request_stop()
        self.assertTrue(self.store.cancel_stop())
        self.assertFalse(self.store.cancel_stop())
        self.assertIsNone(self.store.load()["items"][0]["command"])

    def test_worker_stop_monitor_sets_cancel_event_during_translation(self):
        worker = Worker(self.queue_path)
        worker.activity = "translating"
        worker.start_control_monitor()
        try:
            self.store.request_stop()
            deadline = time.monotonic() + 2
            while not worker.cancel_event.is_set() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(worker.cancel_event.is_set())
        finally:
            worker.stop_control_monitor()

    def test_worker_control_monitor_interrupts_when_current_job_is_paused(self):
        job = make_job("current.pdf")
        job["state"] = "in_progress"
        self.store.set_jobs([job])
        worker = Worker(self.queue_path)
        worker.current_job_id = job["id"]
        worker.activity = "translating"
        worker.start_control_monitor()
        try:
            self.store.update_job(job["id"], state="paused")
            deadline = time.monotonic() + 2
            while not worker.cancel_event.is_set() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(worker.cancel_event.is_set())
        finally:
            worker.stop_control_monitor()

    def test_controller_reports_stopping_only_for_live_worker(self):
        controller = WorkerController(self.queue_path)
        self.store.request_stop()
        with patch.object(controller, "running", return_value=True):
            self.assertTrue(controller.stopping())
            controller.cancel_stop()
            self.assertFalse(controller.stopping())

    def test_ollama_discovery_distinguishes_empty_invalid_and_offline(self):
        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch(
            "doctranslate.queue_app.urllib.request.urlopen",
            return_value=Response(b'{"models": []}'),
        ):
            self.assertEqual(discover_ollama_models().status, "empty")
        with patch(
            "doctranslate.queue_app.urllib.request.urlopen",
            return_value=Response(b'{"unexpected": []}'),
        ):
            self.assertEqual(discover_ollama_models().status, "invalid")
        with patch(
            "doctranslate.queue_app.urllib.request.urlopen",
            side_effect=OSError("offline"),
        ):
            result = discover_ollama_models()
        self.assertEqual(result, OllamaDiscovery("offline", detail="offline"))

    def test_atomic_queue_revision_and_job_order(self):
        first = make_job("first.pdf")
        second = make_job("second.pdf")
        saved = self.store.set_jobs([first, second])
        self.assertEqual(saved["revision"], 1)
        self.assertEqual([job["id"] for job in self.store.jobs()], [first["id"], second["id"]])
        self.assertTrue(self.store.path.is_file())
        self.assertTrue(self.store.path.with_suffix(".bak").is_file() is False)

    def test_queue_transaction_is_structured_logged(self):
        self.store.set_jobs([make_job("book.pdf")])
        log_path = self.queue_path.with_name("queue.events.log")
        records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(record["event"] == "queue.transaction" for record in records))

    def test_stop_is_one_shot(self):
        self.store.set_jobs([make_job("book.pdf")])
        self.store.request_stop()
        self.assertEqual(self.store.load()["items"][0]["command"], "stop")
        self.store.consume_stop()
        self.assertIsNone(self.store.load()["items"][0]["command"])

    def test_lock_is_reusable(self):
        lock_path = Path(self.temp.name) / "queue.lock"
        with FileLock(lock_path):
            self.assertTrue(lock_path.exists())
        self.assertFalse(lock_path.exists())

    def test_dead_process_status_is_read_only(self):
        self.assertEqual(process_status(2**31 - 1), "dead")

    def test_live_child_survives_process_status_probe(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
        try:
            self.assertEqual(process_status(child.pid), "alive")
            self.assertIsNone(child.poll())
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_failed_lock_payload_closes_descriptor_and_removes_own_file(self):
        lock_path = Path(self.temp.name) / "failed.lock"
        lock = FileLock(lock_path)
        with patch("doctranslate.queue_app.os.write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                lock.acquire()
        self.assertIsNone(lock._fd)
        self.assertFalse(lock_path.exists())

    def test_atomic_write_reports_low_space_without_touching_target(self):
        target = Path(self.temp.name) / "state.json"
        target.write_text("original", encoding="utf-8")
        usage = type("Usage", (), {"free": 0})()
        with patch("doctranslate.queue_app.shutil.disk_usage", return_value=usage):
            with self.assertRaises(StorageError):
                atomic_write(target, {"new": True})
        self.assertEqual(target.read_text(encoding="utf-8"), "original")

    def test_atomic_write_reports_replace_failure_and_cleans_temp(self):
        target = Path(self.temp.name) / "state.json"
        target.write_text("original", encoding="utf-8")
        with patch("doctranslate.queue_app.os.replace", side_effect=OSError("access denied")):
            with self.assertRaises(StorageError):
                atomic_write(target, {"new": True})
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertFalse(target.with_name(target.name + ".tmp").exists())

    def test_foreign_lock_is_not_removed_by_release(self):
        lock_path = Path(self.temp.name) / "foreign.lock"
        owner = FileLock(lock_path)
        owner.acquire()
        try:
            foreign = FileLock(lock_path)
            foreign.release()
            self.assertTrue(lock_path.exists())
        finally:
            owner.release()

    def test_concurrent_stale_recovery_has_single_owner(self):
        lock_path = Path(self.temp.name) / "race.lock"
        gate = Path(self.temp.name) / "race.go"
        lock_path.write_text(
            '{"pid": 999999999, "time": "2000-01-01T00:00:00+00:00"}',
            encoding="utf-8",
        )
        script = (
            "\n".join([
                "import sys,time; sys.path.insert(0, sys.argv[2])",
                "from pathlib import Path",
                "from doctranslate.queue_app import FileLock",
                "ready=Path(sys.argv[3]); ready.write_text('ready')",
                "gate=Path(sys.argv[4])",
                "while not gate.exists():",
                "    time.sleep(0.01)",
                "lock=FileLock(Path(sys.argv[1]), timeout=0.15, poll=0.01)",
                "try:",
                "    lock.acquire(); print('owned', flush=True); time.sleep(0.4); lock.release()",
                "except TimeoutError:",
                "    print('blocked', flush=True)",
            ])
        )
        processes = [
            subprocess.Popen(
                [
                    sys.executable, "-c", script, str(lock_path),
                    str(Path(__file__).resolve().parents[1] / "src"),
                    str(Path(self.temp.name) / f"ready-{index}"), str(gate),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for index in range(2)
        ]
        deadline = time.monotonic() + 5
        while not all((Path(self.temp.name) / f"ready-{index}").exists() for index in range(2)):
            if time.monotonic() >= deadline:
                self.fail("lock race subprocesses did not become ready")
            time.sleep(0.01)
        gate.touch()
        results = [process.communicate(timeout=5) for process in processes]
        owned = [stdout.strip() for stdout, _ in results].count("owned")
        blocked = [stdout.strip() for stdout, _ in results].count("blocked")
        self.assertEqual((owned, blocked), (1, 1), results)

    def test_queue_merge_preserves_new_worker_state(self):
        job = make_job("book.pdf")
        self.store.set_jobs([job])
        base = self.store.load()
        draft = [dict(job, model="new-model")]
        self.store.update_job(job["id"], state="done", progress=1.0)
        self.store.merge_jobs(draft, [job], base["revision"])
        current = self.store.jobs()[0]
        self.assertEqual(current["model"], "new-model")
        self.assertEqual(current["state"], "done")
        self.assertEqual(current["progress"], 1.0)

    def test_active_job_delete_is_rejected(self):
        job = make_job("active.pdf")
        job["state"] = "in_progress"
        self.store.set_jobs([job])
        base = self.store.load()
        with self.assertRaises(QueueConflictError):
            self.store.merge_jobs([], [job], base["revision"])

    def test_active_job_delete_is_allowed_after_worker_stopped(self):
        job = make_job("stale-active.pdf")
        job["state"] = "in_progress"
        self.store.set_jobs([job])
        base = self.store.load()
        self.store.merge_jobs([], [job], base["revision"], allow_active_delete=True)
        self.assertEqual(self.store.jobs(), [])

    def test_gui_active_delete_is_published_without_preemptive_stop(self):
        job = make_job("active.pdf")
        calls = []

        class FakeController:
            def running(self):
                return True

            def cancel_stop(self):
                calls.append("cancel_stop")

        fake = type("Gui", (), {
            "jobs_draft": [],
            "base_jobs": [job],
            "store": type("Store", (), {
                "jobs": lambda _self: [job],
            })(),
            "controller": FakeController(),
            "messagebox": type("MessageBox", (), {
                "askyesno": lambda _self, *_args: True,
            })(),
            "_deleted_active_jobs": lambda _self: [job],
            "_publish_draft": lambda _self, **kwargs: calls.append(("publish", kwargs)),
            "_t": lambda _self, key: key,
            "_log_action": lambda _self, *_args, **_kwargs: None,
            "render": lambda _self: None,
        })()

        QueueGui.send(fake)

        self.assertEqual(calls, ["cancel_stop", ("publish", {"allow_active_delete": True})])

    def test_worker_stop_and_pause_are_consumed_after_batch(self):
        stop_job = make_job("stop.pdf")
        stop_job["state"] = "in_progress"
        self.store.set_jobs([stop_job])
        worker = Worker(self.queue_path)
        worker.current_job_id = stop_job["id"]
        self.store.request_stop()
        worker.after_batch()
        self.assertTrue(worker.cancel_event.is_set())

        pause_job = make_job("pause.pdf")
        pause_job["state"] = "in_progress"
        self.store.set_jobs([pause_job])
        worker.current_job_id = pause_job["id"]
        worker.cancel_event.clear()
        self.store.update_job(pause_job["id"], state="paused")
        worker.after_batch()
        self.assertTrue(worker.cancel_event.is_set())

    def test_invalid_job_state_is_rejected(self):
        invalid = make_job("book.pdf")
        invalid["state"] = "mystery"
        with self.assertRaises(ValueError):
            self.store.set_jobs([invalid])

    def test_worker_starts_as_package_module(self):
        controller = WorkerController(self.queue_path)
        with patch.object(controller, "running", return_value=False), patch(
            "doctranslate.queue_app.subprocess.Popen"
        ) as popen:
            self.assertTrue(controller.start())
        command = popen.call_args.args[0]
        self.assertEqual(command[1:3], ["-m", "doctranslate.queue_worker"])
        project_src = str(Path(__file__).resolve().parents[1] / "src")
        self.assertIn(project_src, popen.call_args.kwargs["env"]["PYTHONPATH"].split(";"))

    def test_start_does_not_send_unsent_gui_draft(self):
        calls = []
        fake = type("Fake", (), {
            "dirty": True,
            "controller": type("Controller", (), {"start": lambda self: calls.append("start")})(),
            "store": type("Store", (), {
                "logger": type("Logger", (), {
                    "event": lambda self, *_args, **_kwargs: True,
                })(),
            })(),
            "_log_action": lambda self, *_args, **_kwargs: None,
            "send": lambda self: calls.append("send"),
            "render": lambda self: calls.append("render"),
        })()
        QueueGui.start(fake)
        self.assertEqual(calls, ["start", "render"])

    def test_worker_prefers_in_progress_then_prepared(self):
        prepared = make_job("prepared.pdf")
        progress = make_job("progress.pdf")
        progress["state"] = "in_progress"
        self.store.set_jobs([prepared, progress])
        worker = Worker(self.queue_path)
        self.assertEqual(worker.choose_job()["id"], progress["id"])


if __name__ == "__main__":
    unittest.main()
