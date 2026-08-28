from pathlib import Path
import unittest

from chapter8.knowledge_runtime.catalog import load_documents
from chapter8.knowledge_runtime.chunking import (
    contextualize_chunks,
    fixed_character_chunks,
    structure_aware_chunks,
)
from chapter8.knowledge_runtime.contracts import stable_digest


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "starboard_docs"


def document_named(document_id: str):
    return next(document for document in load_documents(FIXTURE_ROOT) if document.document_id == document_id)


class ChunkingTests(unittest.TestCase):
    def test_fixed_character_chunks_are_bounded_overlapping_and_deterministic(self) -> None:
        document = document_named("migration-2x-to-3.2")
        first = fixed_character_chunks(document, max_chars=90, overlap_chars=15)
        second = fixed_character_chunks(document, max_chars=90, overlap_chars=15)
        self.assertEqual(first, second)
        self.assertGreater(len(first), 2)
        self.assertTrue(all(len(chunk.content) <= 90 for chunk in first))
        self.assertEqual(first[0].content[-15:], first[1].content[:15])

    def test_fixed_character_chunking_rejects_invalid_window(self) -> None:
        document = document_named("plans-3.2")
        with self.assertRaisesRegex(ValueError, "non_positive_max_chars"):
            fixed_character_chunks(document, max_chars=0, overlap_chars=0)
        with self.assertRaisesRegex(ValueError, "invalid_overlap_chars"):
            fixed_character_chunks(document, max_chars=80, overlap_chars=80)

    def test_structure_chunk_keeps_heading_and_table_together(self) -> None:
        document = document_named("plans-3.2")
        chunks = structure_aware_chunks(document, max_chars=520)
        sso = next(chunk for chunk in chunks if "旧式 SAML SSO" in chunk.content)
        self.assertIn("套餐能力", sso.heading_path)
        self.assertIn("| Team | 50 | OIDC |", sso.content)
        self.assertEqual(document.content_digest, sso.document_digest)

    def test_structure_chunk_keeps_fenced_code_block_atomic(self) -> None:
        document = document_named("migration-2x-to-3.2")
        chunks = structure_aware_chunks(document, max_chars=220)
        command = next(chunk for chunk in chunks if "starboard migrate" in chunk.content)
        self.assertEqual(2, command.content.count("```"))
        self.assertIn("执行示例", command.heading_path)

    def test_context_prefix_does_not_change_source_content_or_id(self) -> None:
        document = document_named("plans-3.2")
        source = structure_aware_chunks(document, max_chars=520)
        contextual = contextualize_chunks(document, source)
        self.assertEqual(tuple(chunk.chunk_id for chunk in source), tuple(chunk.chunk_id for chunk in contextual))
        self.assertEqual(tuple(chunk.content for chunk in source), tuple(chunk.content for chunk in contextual))
        self.assertTrue(all(chunk.context_prefix.startswith("文档：") for chunk in contextual))
        self.assertTrue(all(chunk.content_digest == stable_digest(chunk.content) for chunk in contextual))

    def test_structure_chunking_is_deterministic_and_preserves_order(self) -> None:
        document = document_named("faq-3.2-sso")
        first = structure_aware_chunks(document, max_chars=180)
        second = structure_aware_chunks(document, max_chars=180)
        self.assertEqual(first, second)
        self.assertEqual(tuple(range(len(first))), tuple(chunk.ordinal for chunk in first))
        self.assertEqual(len({chunk.chunk_id for chunk in first}), len(first))


if __name__ == "__main__":
    unittest.main()
