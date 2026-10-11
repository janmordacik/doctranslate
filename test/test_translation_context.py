import tempfile
import unittest
from pathlib import Path

from doctranslate.translation.context import ContextBudget, ContextBuilder, ContextTooLargeError
from doctranslate.translation.memory import GlossaryEntry, GlossarySnapshot
from doctranslate.translation.retrieval import GlossaryIndex, SourceOccurrence, search_occurrences


class ExactCounter:
    def count(self, text):
        return len(text)


def entry(key, source, target, sense="", scope=""):
    return GlossaryEntry(key, source, target, "en", "cs", sense, scope, "manual", 1)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = GlossarySnapshot(
            revision=3,
            entries=(
                entry("bank-finance", "bank", "banka", "finance"),
                entry("bank-river", "bank", "břeh", "river"),
                entry("book", "book", "kniha"),
            ),
        )

    def test_index_filters_language_sense_and_ranks_aliases_deterministically(self):
        index = GlossaryIndex(self.snapshot, {"bank-finance": ("financial institution",)})
        results, more = index.search("A financial institution", "en", "cs", sense="finance", limit=2)
        self.assertFalse(more)
        self.assertEqual([item.entry.target_term for item in results], ["banka"])

    def test_occurrences_are_bounded_and_stably_ranked(self):
        occurrences = (
            SourceOccurrence("b", "same phrase", "dva"),
            SourceOccurrence("a", "same phrase", "jedna"),
            SourceOccurrence("c", "other", "jiné"),
        )
        found, more = search_occurrences("same phrase", occurrences, limit=1)
        self.assertTrue(more)
        self.assertEqual(found[0].occurrence.segment_id, "a")

    def test_source_overflow_is_not_silently_truncated(self):
        builder = ContextBuilder(ExactCounter())
        with self.assertRaises(ContextTooLargeError):
            builder.build("123456", "en", "cs", budget=ContextBudget(5))

    def test_builder_returns_only_relevant_bounded_context(self):
        builder = ContextBuilder(ExactCounter())
        envelope = builder.build(
            "bank details", "en", "cs",
            budget=ContextBudget(70, instruction_tokens=2, schema_tokens=2, reserved_output_tokens=4),
            instructions="translate only", memory=self.snapshot,
            occurrences=(SourceOccurrence("s1", "bank details", "údaje o bance", 4),
                         SourceOccurrence("s2", "unrelated", "nesouvisející", 5)),
            sense="finance", glossary_limit=2, occurrence_limit=2,
        )
        self.assertEqual(envelope.source_text, "bank details")
        self.assertEqual(envelope.instructions, "translate only")
        self.assertEqual([item.entry.target_term for item in envelope.glossary], ["banka"])
        self.assertEqual([item.segment_id for item in envelope.occurrences], ["s1"])
        payload = envelope.to_mapping()
        self.assertEqual(payload["source"]["text"], "bank details")
        self.assertNotIn("unrelated", payload["source"]["text"])
        self.assertEqual(payload["context"]["occurrences"][0]["page_number"], 4)

    def test_memory_larger_than_prompt_sets_more_indicators(self):
        builder = ContextBuilder(ExactCounter())
        many = GlossarySnapshot(entries=tuple(
            entry(str(i), "term" + str(i), "pojem" + str(i)) for i in range(5)
        ))
        envelope = builder.build("term0", "en", "cs", budget=ContextBudget(18), memory=many, glossary_limit=5)
        self.assertTrue(envelope.glossary_more)
        self.assertLessEqual(envelope.content_tokens, 12)


if __name__ == "__main__":
    unittest.main()
