import unittest

from doctranslate.translate_core.contracts import XhtmlBlock
from doctranslate.translation.planning import (
    ConservativeTokenCounter,
    PlanningBudget,
    SegmentTooLargeError,
    SemanticBatchPlanner,
    flatten_parts,
)


def block(block_id, text, page=1, **attributes):
    return XhtmlBlock(block_id, page, int(block_id[1:]) if block_id[1:].isdigit() else 1,
                      text, markup="<p>" + text + "</p>", attributes=attributes)


class ExactCounter:
    def count(self, text):
        return len(text)


class PlanningTests(unittest.TestCase):
    def test_budget_reserves_are_not_available_to_source_text(self):
        budget = PlanningBudget(20, instruction_tokens=2, schema_tokens=3, reserved_output_tokens=4)
        self.assertEqual(budget.input_tokens, 11)

    def test_packs_in_order_and_keeps_stable_mapping(self):
        planner = SemanticBatchPlanner(ExactCounter())
        blocks = [block("b1", "one"), block("b2", "two"), block("b3", "three")]
        segments = planner.plan(blocks, PlanningBudget(11))
        self.assertEqual([item.source_block_ids for item in segments],
                         [("b1", "b2"), ("b3",)])
        self.assertEqual(segments[0].input_text, "one\n\ntwo")
        self.assertEqual([item.segment_id for item in segments],
                         ["b1:segment:0", "b3:segment:0"])
        self.assertEqual([item.source_block_id for item in flatten_parts(segments)],
                         ["b1", "b2", "b3"])

    def test_oversized_block_splits_at_sentences_without_loss(self):
        text = "First sentence. Second sentence. Third sentence."
        planner = SemanticBatchPlanner(ExactCounter())
        segments = planner.plan([block("b1", text)], PlanningBudget(20))
        parts = flatten_parts(segments)
        self.assertEqual("".join(item.text for item in parts), text)
        self.assertEqual([item.part_id for item in parts], ["b1:0", "b1:1", "b1:2"])
        self.assertEqual(tuple(item.source_block_id for item in parts), ("b1", "b1", "b1"))

    def test_protected_fragment_prevents_sentence_split_inside_literal(self):
        text = "Mr. Smith arrived. Next sentence."
        planner = SemanticBatchPlanner(ExactCounter())
        segments = planner.plan(
            [block("b1", text, protected_fragments=("Mr.",))], PlanningBudget(22)
        )
        parts = flatten_parts(segments)
        self.assertEqual("".join(item.text for item in parts), text)
        self.assertEqual(parts[0].text, "Mr. Smith arrived. ")

    def test_single_oversized_sentence_fails_explicitly(self):
        planner = SemanticBatchPlanner(ExactCounter())
        with self.assertRaises(SegmentTooLargeError):
            planner.plan([block("b1", "one very long sentence")], PlanningBudget(5))

    def test_empty_block_is_preserved_and_page_is_metadata_only(self):
        planner = SemanticBatchPlanner(ExactCounter())
        empty = block("b1", "", page=7)
        segment = planner.plan([empty], PlanningBudget(5))[0]
        self.assertEqual(segment.input_text, "")
        self.assertEqual(segment.page_numbers, (7,))
        self.assertNotIn("7", segment.input_text)

    def test_fallback_marks_estimated_accounting(self):
        estimate = ConservativeTokenCounter().count("abcd")
        self.assertEqual(estimate, 2)
        segment = SemanticBatchPlanner().plan([block("b1", "abcd")], PlanningBudget(4))[0]
        self.assertEqual(segment.token_method, "estimated")


if __name__ == "__main__":
    unittest.main()
