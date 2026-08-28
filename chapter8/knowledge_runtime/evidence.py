from __future__ import annotations

from chapter8.knowledge_runtime.contracts import (
    AnswerDecision,
    AnswerStatus,
    Citation,
    EvidencePacket,
    QuestionCase,
    RetrievalHit,
    RetrievalQuery,
    TrustLevel,
)


def _safe_for_answer(hit: RetrievalHit) -> bool:
    if "malicious-instruction" in hit.chunk.fact_ids:
        return False
    if hit.chunk.trust is TrustLevel.COMMUNITY and "忽略其他来源" in hit.chunk.content:
        return False
    return True


def build_evidence_packet(
    query: RetrievalQuery,
    hits: tuple[RetrievalHit, ...],
    required_fact_ids: tuple[str, ...],
) -> EvidencePacket:
    evidence: list[RetrievalHit] = []
    seen: set[str] = set()
    for hit in hits:
        if hit.chunk.chunk_id in seen or not _safe_for_answer(hit):
            continue
        seen.add(hit.chunk.chunk_id)
        evidence.append(hit)

    citations = tuple(
        Citation(
            citation_id=f"C{index}",
            document_id=hit.chunk.document_id,
            chunk_id=hit.chunk.chunk_id,
            source_path=hit.chunk.source_path,
            version=hit.chunk.version_min,
            content_digest=hit.chunk.content_digest,
            fact_ids=hit.chunk.fact_ids,
        )
        for index, hit in enumerate(evidence, start=1)
    )
    available = {fact_id for citation in citations for fact_id in citation.fact_ids}
    present = tuple(fact_id for fact_id in required_fact_ids if fact_id in available)
    missing = tuple(fact_id for fact_id in required_fact_ids if fact_id not in available)
    return EvidencePacket(
        query=query,
        citations=citations,
        evidence=tuple(evidence),
        present_fact_ids=present,
        missing_fact_ids=missing,
    )


class ScriptedAnswerPolicy:
    """Freezes answer decisions so experiments compare harness behavior, not a model."""

    def answer(self, case: QuestionCase, packet: EvidencePacket) -> AnswerDecision:
        citation_ids = tuple(citation.citation_id for citation in packet.citations)
        if packet.missing_fact_ids and packet.present_fact_ids:
            return AnswerDecision(
                status=AnswerStatus.PARTIAL,
                claims=(),
                citation_ids=citation_ids,
                missing_fact_ids=packet.missing_fact_ids,
                reason="partial_evidence",
            )
        if packet.missing_fact_ids or not packet.citations:
            return AnswerDecision(
                status=AnswerStatus.ABSTAIN,
                claims=(),
                citation_ids=(),
                missing_fact_ids=packet.missing_fact_ids,
                reason="insufficient_evidence",
            )
        return AnswerDecision(
            status=AnswerStatus.ANSWER,
            claims=case.expected_claims,
            citation_ids=citation_ids,
            missing_fact_ids=(),
            reason="required_evidence_present",
        )
