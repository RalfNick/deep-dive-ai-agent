import math
import unittest

from chapter8.knowledge_runtime.evaluation import (
    answer_support_metrics,
    citation_metrics,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


class EvaluationTests(unittest.TestCase):
    def test_retrieval_metrics_match_hand_calculated_example(self) -> None:
        retrieved = ("a", "noise", "b")
        relevant = {"a", "b"}
        self.assertAlmostEqual(2 / 3, precision_at_k(retrieved, relevant, 3))
        self.assertEqual(1.0, recall_at_k(retrieved, relevant, 3))
        self.assertEqual(1.0, mean_reciprocal_rank(retrieved, relevant))
        expected_ndcg = (1.0 + 1.0 / math.log2(4)) / (1.0 + 1.0 / math.log2(3))
        self.assertAlmostEqual(expected_ndcg, ndcg_at_k(retrieved, relevant, 3))

    def test_empty_relevance_returns_none_instead_of_fabricated_zero(self) -> None:
        self.assertIsNone(recall_at_k(("a",), set(), 1))
        self.assertIsNone(mean_reciprocal_rank(("a",), set()))
        self.assertIsNone(ndcg_at_k(("a",), set(), 1))

    def test_precision_at_k_uses_k_as_the_denominator_even_with_fewer_results(self) -> None:
        self.assertAlmostEqual(1 / 3, precision_at_k(("a", "noise"), {"a"}, 3))
        self.assertEqual(0.0, precision_at_k((), {"a"}, 3))

    def test_wrong_citation_counts_as_neither_precise_nor_recalled(self) -> None:
        expected = {"claim-sso": {"C1"}, "claim-members": {"C2"}}
        actual = {"claim-sso": {"C1"}, "claim-members": {"C3"}}
        metrics = citation_metrics(expected, actual)
        self.assertEqual(0.5, metrics.precision)
        self.assertEqual(0.5, metrics.recall)
        self.assertEqual(0.5, metrics.supported_claim_ratio)

    def test_answer_support_separates_missing_and_unsupported_claims(self) -> None:
        metrics = answer_support_metrics(
            required_fact_ids=("sso-team-32", "members-preserved-32"),
            present_fact_ids=("sso-team-32",),
            answered=True,
        )
        self.assertEqual(0.5, metrics.supported_fact_ratio)
        self.assertEqual(1, metrics.unsupported_claim_count)
        self.assertEqual(("members-preserved-32",), metrics.missing_fact_ids)


if __name__ == "__main__":
    unittest.main()
