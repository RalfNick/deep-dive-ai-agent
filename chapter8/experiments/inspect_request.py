"""Inspect one real offline request; stdout only, no API calls or report writes."""

from dataclasses import asdict
import json
import sys

from chapter8.experiments.run_all import _case_map, _retriever
from chapter8.knowledge_runtime.evidence import ScriptedAnswerPolicy, build_evidence_packet


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    case = _case_map()["governance-compound-upgrade"]
    hits, trace = _retriever().retrieve(case.query, include_trace=True)
    packet = build_evidence_packet(case.query, hits, case.required_fact_ids)
    decision = ScriptedAnswerPolicy().answer(case, packet)
    print(json.dumps({
        "question": case.query.text,
        "evidence": [{
            "citation_id": citation.citation_id,
            "document_id": hit.chunk.document_id,
            "heading_path": hit.chunk.heading_path,
            "content": hit.chunk.content,
            "fact_ids": hit.chunk.fact_ids,
        } for citation, hit in zip(packet.citations, packet.evidence)],
        "present_fact_ids": packet.present_fact_ids,
        "missing_fact_ids": packet.missing_fact_ids,
        "decision": asdict(decision),
        "trace": asdict(trace),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
