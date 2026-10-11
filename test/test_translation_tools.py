import tempfile
import unittest
from pathlib import Path

from doctranslate.translation.memory import JsonGlossaryStore
from doctranslate.translation.retrieval import SourceOccurrence
from doctranslate.translation.tools import MemoryToolError, MemoryTools


class _ExplodingStore:
    def load(self):
        raise AssertionError("invalid input must be rejected before store access")


class MemoryToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = JsonGlossaryStore(Path(self.temp.name) / "glossary.json")
        self.occurrences = (
            SourceOccurrence("s1", "bank", "banka", 1),
            SourceOccurrence("s2", "bank account", "bankovní účet", 2),
            SourceOccurrence("s3", "unrelated text", "nesouvisející text", 3),
        )
        self.tools = MemoryTools(self.store, occurrences=self.occurrences)

    def tearDown(self):
        self.temp.cleanup()

    def _accept(self, source, target, *, scope=""):
        current = self.store.load().revision
        proposal = self.store.propose(
            source,
            target,
            "en",
            "cs",
            scope=scope,
            expected_revision=current,
        )
        return self.store.accept(proposal.proposal_id, expected_revision=current + 1)

    def test_lookup_is_bounded_and_keeps_revision(self):
        self._accept("bank", "banka")
        self._accept("bank account", "bankovní účet")
        result = self.tools.lookup_terms(
            ["bank", "bank account"],
            {"source_language": "en", "target_language": "cs"},
            limit=1,
        )
        self.assertEqual(result.revision, self.store.load().revision)
        self.assertEqual(len(result.matches), 1)
        self.assertTrue(result.more)
        self.assertEqual(result.matches[0].entry.target_term, "bankovní účet")

    def test_scope_and_search_memory_are_separate(self):
        self._accept("bank", "banka", scope="finance")
        result = self.tools.lookup_terms(
            "bank",
            source_language="en",
            target_language="cs",
            scope="finance",
        )
        self.assertEqual([item.entry.target_term for item in result.matches], ["banka"])
        history = self.tools.search_memory("finance", limit=4)
        self.assertGreaterEqual(len(history.records), 1)
        self.assertTrue(all("finance" in record.text for record in history.records))

    def test_occurrences_and_source_are_bounded(self):
        occurrences = self.tools.get_occurrences("bank", limit=1)
        self.assertEqual(len(occurrences.matches), 1)
        self.assertTrue(occurrences.more)
        source = self.tools.get_source(["s1", "s2"], limit=1)
        self.assertEqual([item.segment_id for item in source.segments], ["s1"])
        self.assertTrue(source.more)
        with self.assertRaises(MemoryToolError) as error:
            self.tools.get_source("missing")
        self.assertEqual(error.exception.code, "unknown_segment")

    def test_proposal_carries_evidence_and_explicit_accept_is_cas(self):
        result = self.tools.propose_term(
            {
                "source_term": "orbit",
                "target_term": "oběžná dráha",
                "source_language": "en",
                "target_language": "cs",
            },
            evidence=["s1"],
            expected_revision=0,
        )
        self.assertEqual(result.evidence, ("s1",))
        self.assertEqual(result.dirty_segment_ids, ("s1",))
        entry_result = self.tools.accept_proposal(
            result.proposal.proposal_id,
            expected_revision=result.revision,
        )
        self.assertEqual(entry_result.entry.evidence, ("s1",))
        self.assertEqual(entry_result.status, "accepted")
        with self.assertRaises(MemoryToolError) as error:
            self.tools.accept_proposal(
                result.proposal.proposal_id,
                expected_revision=result.revision,
            )
        self.assertEqual(error.exception.code, "revision_conflict")

    def test_reject_is_explicit_and_does_not_add_entry(self):
        current = self.store.load().revision
        result = self.tools.propose_term(
            {
                "source_term": "draft",
                "target_term": "návrh",
                "source_language": "en",
                "target_language": "cs",
            },
            expected_revision=current,
        )
        rejected = self.tools.reject_proposal(
            result.proposal.proposal_id,
            expected_revision=result.revision,
        )
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(self.store.load().entries, ())
        self.assertEqual(self.store.load().proposals[0].status, "rejected")

    def test_rejected_proposal_cannot_be_accepted_or_rejected_accepted_entry(self):
        current = self.store.load().revision
        result = self.tools.propose_term(
            {
                "source_term": "closed",
                "target_term": "uzavřený",
                "source_language": "en",
                "target_language": "cs",
            },
            expected_revision=current,
        )
        self.tools.reject_proposal(
            result.proposal.proposal_id,
            expected_revision=result.revision,
        )
        with self.assertRaises(MemoryToolError) as error:
            self.tools.accept_proposal(
                result.proposal.proposal_id,
                expected_revision=self.store.load().revision,
            )
        self.assertEqual(error.exception.code, "conflict")
        accepted_proposal = self.store.propose(
            "accepted",
            "schválený",
            "en",
            "cs",
            expected_revision=self.store.load().revision,
        )
        self.store.accept(
            accepted_proposal.proposal_id,
            expected_revision=self.store.load().revision,
        )
        with self.assertRaises(MemoryToolError) as error:
            self.tools.reject_proposal(
                accepted_proposal.proposal_id,
                expected_revision=self.store.load().revision,
            )
        self.assertEqual(error.exception.code, "conflict")


    def test_revision_request_marks_segments_without_ai_loop(self):
        request = self.tools.request_revision(["s1", "s2"], "Terminology mismatch")
        self.assertEqual(request.segment_ids, ("s1", "s2"))
        self.assertEqual(self.tools.dirty_segment_ids, ("s1", "s2"))
        self.assertEqual(request.revision, self.store.load().revision)

    def test_dispatch_allowlist_and_mapping_arguments(self):
        self._accept("term", "pojem")
        result = self.tools.dispatch(
            "lookup_terms",
            {
                "terms": "term",
                "context": {"source_language": "en", "target_language": "cs"},
            },
        )
        self.assertEqual(len(result.matches), 1)
        with self.assertRaises(MemoryToolError) as error:
            self.tools.dispatch("open_file", {"path": "glossary.json"})
        self.assertEqual(error.exception.code, "unknown_tool")

    def test_invalid_arguments_do_not_touch_store(self):
        tools = MemoryTools(_ExplodingStore())
        with self.assertRaises(MemoryToolError) as error:
            tools.lookup_terms("", source_language="en", target_language="cs")
        self.assertEqual(error.exception.code, "invalid_schema")
        with self.assertRaises(MemoryToolError) as error:
            tools.get_source([""])
        self.assertEqual(error.exception.code, "invalid_schema")
        with self.assertRaises(MemoryToolError) as error:
            tools.propose_term(
                {"source_term": "x", "target_term": "y", "source_language": "en", "target_language": "cs"}
            )
        self.assertEqual(error.exception.code, "missing_revision")

    def test_large_result_is_limited_by_tokens(self):
        self._accept("long", "velmi dlouhý cílový termín")
        result = self.tools.lookup_terms(
            "long",
            source_language="en",
            target_language="cs",
            token_limit=1,
        )
        self.assertEqual(result.matches, ())
        self.assertTrue(result.more)


if __name__ == "__main__":
    unittest.main()
