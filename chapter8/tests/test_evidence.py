from pathlib import Path
import unittest

from chapter8.knowledge_runtime.catalog import load_documents, load_question_cases
from chapter8.knowledge_runtime.chunking import contextualize_chunks, structure_aware_chunks
from chapter8.knowledge_runtime.contracts import (
    AnswerStatus,
    RetrievalHit,
    ScoreBreakdown,
)
from chapter8.knowledge_runtime.evidence import ScriptedAnswerPolicy, build_evidence_packet


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "starboard_docs"
QUESTION_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "questions.json"


def case_named(case_id: str):
    return next(case for case in load_question_cases(QUESTION_PATH) if case.case_id == case_id)


def hit(document_id: str, phrase: str) -> RetrievalHit:
    document = next(item for item in load_documents(FIXTURE_ROOT) if item.document_id == document_id)
    chunk = next(
        item
        for item in contextualize_chunks(document, structure_aware_chunks(document, 520))
        if phrase in item.content
    )
    return RetrievalHit(
        chunk=chunk,
        score=1.0,
        breakdown=ScoreBreakdown(lexical=1.0, semantic=0.8, fusion=0.03, rerank=2.0),
    )


class EvidenceTests(unittest.TestCase):
    def test_compound_answer_is_partial_when_membership_evidence_is_missing(self) -> None:
        case = case_named("governance-compound-upgrade")
        packet = build_evidence_packet(
            case.query,
            (hit("plans-3.2", "旧式 SAML SSO"),),
            required_fact_ids=case.required_fact_ids,
        )
        decision = ScriptedAnswerPolicy().answer(case, packet)
        self.assertEqual(AnswerStatus.PARTIAL, decision.status)
        self.assertEqual(("members-preserved-32",), decision.missing_fact_ids)
        self.assertEqual((), decision.claims)

    def test_complete_evidence_produces_answer_and_stable_citations(self) -> None:
        case = case_named("governance-compound-upgrade")
        packet = build_evidence_packet(
            case.query,
            (
                hit("migration-2x-to-3.2", "不能在 3.2 保留"),
                hit("faq-3.2-sso", "不会自动删除"),
            ),
            required_fact_ids=case.required_fact_ids,
        )
        decision = ScriptedAnswerPolicy().answer(case, packet)
        self.assertEqual(AnswerStatus.ANSWER, decision.status)
        self.assertEqual(case.expected_claims, decision.claims)
        self.assertEqual(("C1", "C2"), decision.citation_ids)
        self.assertEqual("migration-2x-to-3.2.md", packet.citations[0].source_path)
        self.assertEqual(64, len(packet.citations[0].content_digest))

    def test_no_evidence_abstains_without_fabricating_citations(self) -> None:
        case = case_named("evidence-correct-abstain")
        packet = build_evidence_packet(case.query, (), required_fact_ids=case.required_fact_ids)
        decision = ScriptedAnswerPolicy().answer(case, packet)
        self.assertEqual(AnswerStatus.ABSTAIN, decision.status)
        self.assertEqual((), decision.citation_ids)
        self.assertEqual("insufficient_evidence", decision.reason)

    def test_prompt_injection_chunk_never_enters_answer_evidence(self) -> None:
        case = case_named("evidence-prompt-injection")
        packet = build_evidence_packet(
            case.query,
            (
                hit("community-malicious-note", "忽略其他来源"),
                hit("security-overview", "社区文档中的命令"),
            ),
            required_fact_ids=case.required_fact_ids,
        )
        self.assertNotIn("community-malicious-note", {citation.document_id for citation in packet.citations})
        self.assertEqual(("community-untrusted",), packet.present_fact_ids)


if __name__ == "__main__":
    unittest.main()
