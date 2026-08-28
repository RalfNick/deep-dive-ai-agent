from dataclasses import FrozenInstanceError
import unittest

from chapter8.knowledge_runtime.contracts import (
    AnswerStatus,
    Chunk,
    DocumentStatus,
    KnowledgeDocument,
    QuestionCase,
    RetrievalQuery,
    TrustLevel,
    Visibility,
    stable_digest,
)


def valid_document(**overrides: object) -> KnowledgeDocument:
    values: dict[str, object] = {
        "document_id": "plans-3.2",
        "title": "星舟工作台 3.2 套餐说明",
        "source_path": "plans-3.2.md",
        "version_min": "3.2",
        "version_max": "3.2",
        "valid_from": "2026-07-01T00:00:00Z",
        "valid_until": None,
        "allowed_roles": ("public", "member", "admin"),
        "source_type": "product-doc",
        "status": DocumentStatus.ACTIVE,
        "visibility": Visibility.PUBLIC,
        "trust": TrustLevel.AUTHORITATIVE,
        "fact_ids": ("sso-32",),
        "content": "# 套餐说明\n\nTeam 版不再包含旧式 SSO。",
    }
    values.update(overrides)
    return KnowledgeDocument(**values)


class ContractTests(unittest.TestCase):
    def test_document_rejects_blank_id_invalid_time_and_empty_roles(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank_document_id"):
            valid_document(document_id="")
        with self.assertRaisesRegex(ValueError, "invalid_valid_from"):
            valid_document(valid_from="tomorrow")
        with self.assertRaisesRegex(ValueError, "empty_allowed_roles"):
            valid_document(allowed_roles=())

    def test_document_rejects_bad_version_window_and_digest(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid_version_min"):
            valid_document(version_min="latest")
        with self.assertRaisesRegex(ValueError, "version_window_reversed"):
            valid_document(version_min="3.2", version_max="2.8")
        with self.assertRaisesRegex(ValueError, "content_digest_mismatch"):
            valid_document(content_digest="0" * 64)

    def test_document_filters_time_version_and_role(self) -> None:
        document = valid_document(valid_until="2026-08-01T00:00:00Z")
        self.assertTrue(document.valid_at("2026-07-31T23:59:59Z"))
        self.assertFalse(document.valid_at("2026-08-01T00:00:00Z"))
        self.assertTrue(document.supports_version("3.2"))
        self.assertFalse(document.supports_version("2.8"))
        self.assertTrue(document.visible_to("public"))
        self.assertFalse(document.visible_to("maintainer"))

    def test_chunk_id_is_stable_and_keeps_parent_digest(self) -> None:
        document = valid_document()
        chunk = Chunk.from_document(
            document,
            ordinal=0,
            heading_path=("套餐能力", "SSO"),
            content="Team 版不再包含旧式 SSO。",
            context_prefix="文档：星舟工作台 3.2 套餐说明",
        )
        same = Chunk.from_document(
            document,
            ordinal=0,
            heading_path=("套餐能力", "SSO"),
            content="Team 版不再包含旧式 SSO。",
            context_prefix="文档：星舟工作台 3.2 套餐说明",
        )
        changed = Chunk.from_document(
            document,
            ordinal=1,
            heading_path=("套餐能力", "SSO"),
            content="Team 版不再包含旧式 SSO。",
        )
        self.assertEqual(chunk.chunk_id, same.chunk_id)
        self.assertNotEqual(chunk.chunk_id, changed.chunk_id)
        self.assertEqual(document.content_digest, chunk.document_digest)
        self.assertEqual(stable_digest(chunk.content), chunk.content_digest)

    def test_query_rejects_blank_fields_bad_time_and_non_positive_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank_query_text"):
            RetrievalQuery("", "public", "3.2", "2026-07-10T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "invalid_query_time"):
            RetrievalQuery("SSO", "public", "3.2", "today")
        with self.assertRaisesRegex(ValueError, "non_positive_top_k"):
            RetrievalQuery("SSO", "public", "3.2", "2026-07-10T00:00:00Z", top_k=0)
        with self.assertRaisesRegex(ValueError, "candidate_k_below_top_k"):
            RetrievalQuery("SSO", "public", "3.2", "2026-07-10T00:00:00Z", top_k=4, candidate_k=3)

    def test_question_case_rejects_missing_truth_and_status_mismatch(self) -> None:
        query = RetrievalQuery("升级后还能用旧式 SSO 吗？", "public", "3.2", "2026-07-10T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "blank_case_id"):
            QuestionCase("", query, ("plans-3.2",), (), ("sso-32",), ("不能",), AnswerStatus.ANSWER)
        with self.assertRaisesRegex(ValueError, "answer_case_requires_claims"):
            QuestionCase("q1", query, ("plans-3.2",), (), ("sso-32",), (), AnswerStatus.ANSWER)
        with self.assertRaisesRegex(ValueError, "abstain_case_has_claims"):
            QuestionCase("q2", query, (), (), (), ("猜测",), AnswerStatus.ABSTAIN)

    def test_records_are_frozen(self) -> None:
        document = valid_document()
        with self.assertRaises(FrozenInstanceError):
            document.title = "被修改"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
