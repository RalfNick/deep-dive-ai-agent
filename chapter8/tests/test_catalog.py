from pathlib import Path
import json
from tempfile import TemporaryDirectory
import unittest

from chapter8.knowledge_runtime.catalog import KnowledgeCatalog, load_documents, load_question_cases
from chapter8.knowledge_runtime.contracts import RetrievalQuery


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "starboard_docs"
QUESTION_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "questions.json"


def query(
    *,
    role: str = "public",
    target_version: str = "3.2",
    now: str = "2026-08-27T16:00:00Z",
) -> RetrievalQuery:
    return RetrievalQuery(
        text="从 2.8 升级到 3.2 后，Team 版还能保留旧式 SSO 吗，成员会被删除吗？",
        role=role,
        target_version=target_version,
        now=now,
        top_k=3,
        candidate_k=8,
    )


class CatalogTests(unittest.TestCase):
    def test_fixture_has_exactly_eighteen_document_metadata_pairs(self) -> None:
        documents = load_documents(FIXTURE_ROOT)
        self.assertEqual(18, len(documents))
        self.assertEqual(18, len(tuple(FIXTURE_ROOT.glob("*.md"))))
        self.assertEqual(18, len(tuple(FIXTURE_ROOT.glob("*.meta.json"))))
        self.assertEqual(18, len({document.document_id for document in documents}))

    def test_public_32_query_excludes_retired_future_and_internal_docs(self) -> None:
        catalog = KnowledgeCatalog(load_documents(FIXTURE_ROOT))
        ids = {document.document_id for document in catalog.current_documents(query())}
        self.assertIn("plans-3.2", ids)
        self.assertIn("migration-2x-to-3.2", ids)
        self.assertNotIn("faq-2.8-sso", ids)
        self.assertNotIn("maintainer-sso-bypass", ids)
        self.assertNotIn("plans-3.3-preview", ids)
        self.assertNotIn("withdrawn-draft", ids)

    def test_version_and_role_are_hard_filters(self) -> None:
        catalog = KnowledgeCatalog(load_documents(FIXTURE_ROOT))
        public_28 = {document.document_id for document in catalog.current_documents(query(target_version="2.8"))}
        admin_32 = {document.document_id for document in catalog.current_documents(query(role="admin"))}
        self.assertNotIn("plans-3.2", public_28)
        self.assertIn("sso-admin-guide", admin_32)
        self.assertNotIn("sso-admin-guide", {document.document_id for document in catalog.current_documents(query())})

    def test_catalog_withdrawal_overrides_loaded_document(self) -> None:
        catalog = KnowledgeCatalog(load_documents(FIXTURE_ROOT))
        self.assertIsNotNone(catalog.resolve_document("community-malicious-note", query()))
        catalog.withdraw("community-malicious-note")
        self.assertIsNone(catalog.resolve_document("community-malicious-note", query()))

    def test_loader_rejects_orphan_unknown_field_and_digest_mismatch(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unpaired_fixture"):
                load_documents(root)

            (root / "orphan.meta.json").write_text(
                json.dumps(
                    {
                        "document_id": "orphan",
                        "title": "Orphan",
                        "version_min": "3.2",
                        "version_max": "3.2",
                        "valid_from": "2026-07-01T00:00:00Z",
                        "valid_until": None,
                        "allowed_roles": ["public"],
                        "source_type": "product-doc",
                        "status": "active",
                        "visibility": "public",
                        "trust": "authoritative",
                        "fact_ids": [],
                        "content_digest": "0" * 64,
                        "unexpected": True,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unknown_metadata_fields"):
                load_documents(root)
            payload = json.loads((root / "orphan.meta.json").read_text(encoding="utf-8"))
            payload.pop("unexpected")
            (root / "orphan.meta.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "content_digest_mismatch"):
                load_documents(root)

    def test_question_fixture_has_twenty_typed_cases_and_compound_truth(self) -> None:
        cases = load_question_cases(QUESTION_PATH)
        self.assertEqual(20, len(cases))
        compound = next(case for case in cases if case.case_id == "governance-compound-upgrade")
        self.assertEqual(("sso-team-32", "members-preserved-32"), compound.required_fact_ids)
        self.assertEqual("3.2", compound.query.target_version)


if __name__ == "__main__":
    unittest.main()
