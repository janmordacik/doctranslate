import json
import tempfile
import unittest
from pathlib import Path

from doctranslate.translation.memory import (
    GlossaryError,
    JsonGlossaryStore,
    glossary_key,
)


class GlossaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "glossary.json"
        self.store = JsonGlossaryStore(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_store_and_key_include_scope_and_sense(self):
        self.assertEqual(self.store.load().revision, 0)
        self.assertNotEqual(
            glossary_key("bank", "en", "cs", sense="finance"),
            glossary_key("bank", "en", "cs", sense="river"),
        )

    def test_propose_accept_lookup_and_history(self):
        proposal = self.store.propose("bank", "banka", "en", "cs", sense="finance")
        self.assertEqual(proposal.status, "proposed")
        entry = self.store.accept(proposal.proposal_id, expected_revision=1)
        self.assertEqual(entry.target_term, "banka")
        found = self.store.lookup("BANK", "en", "cs", sense="finance")
        self.assertEqual(found, entry)
        snapshot = self.store.load()
        self.assertEqual(snapshot.revision, 2)
        self.assertEqual([item["kind"] for item in snapshot.history], ["proposal", "accepted"])

    def test_repeated_proposal_is_idempotent(self):
        first = self.store.propose("term", "pojem", "en", "cs")
        second = self.store.propose(" term ", "POJEM", "en", "cs")
        self.assertEqual(first.proposal_id, second.proposal_id)
        self.assertEqual(self.store.load().revision, 1)
        self.assertEqual(len(self.store.load().proposals), 1)

    def test_conflict_does_not_overwrite_accepted_entry(self):
        proposal = self.store.propose("term", "pojem", "en", "cs")
        self.store.accept(proposal.proposal_id)
        conflict = self.store.propose("term", "výraz", "en", "cs")
        self.assertEqual(conflict.status, "conflict")
        self.assertEqual(self.store.lookup("term", "en", "cs").target_term, "pojem")
        with self.assertRaises(GlossaryError) as error:
            self.store.accept(conflict.proposal_id)
        self.assertEqual(error.exception.code, "conflict")

    def test_compare_and_swap_rejects_stale_revision(self):
        self.store.propose("one", "jedna", "en", "cs")
        with self.assertRaises(GlossaryError) as error:
            self.store.propose("two", "dva", "en", "cs", expected_revision=0)
        self.assertEqual(error.exception.code, "revision_conflict")

    def test_invalid_json_is_safe_error_and_does_not_rewrite(self):
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(GlossaryError) as error:
            self.store.load()
        self.assertEqual(error.exception.code, "storage_error")
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")

    def test_writer_failure_is_typed_and_keeps_previous_file(self):
        self.store.propose("one", "jedna", "en", "cs")
        old = self.path.read_text(encoding="utf-8")
        failing = JsonGlossaryStore(self.path, atomic_writer=lambda _path, _text: (_ for _ in ()).throw(OSError("full")))
        with self.assertRaises(GlossaryError) as error:
            failing.propose("two", "dva", "en", "cs")
        self.assertEqual(error.exception.code, "storage_error")
        self.assertEqual(self.path.read_text(encoding="utf-8"), old)

    def test_busy_lock_is_reported(self):
        self.store.lock_path.write_text("other", encoding="ascii")
        busy = JsonGlossaryStore(self.path, lock_timeout=0)
        with self.assertRaises(GlossaryError) as error:
            busy.propose("one", "jedna", "en", "cs")
        self.assertEqual(error.exception.code, "lock_timeout")


if __name__ == "__main__":
    unittest.main()
