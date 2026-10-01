from dataclasses import replace
import pytest
from chapter18.tests.helpers import ROOT, packet
from chapter18.contracts import Claim, EvidenceRef, ToolCall
from chapter18.fixtures import load_sources


def claim(source_id="public-current", key="sharing", value="支持"):
    source = next(s for s in load_sources(ROOT) if s.source_id == source_id)
    quote = next(line for line in source.text.splitlines() if value in line and not line.startswith("#"))
    return Claim(key, value, (EvidenceRef(source.source_id, source.location, source.digest, source.version, source.eligible, quote),))


def test_three_votes_count_one_source_not_three_and_cannot_support_wrong_value():
    from chapter18.evidence import check_claims
    c = claim()
    verdict = check_claims(packet(), (c, c, c), load_sources(ROOT))
    assert verdict.status == "answer" and verdict.distinct_sources == ("public-current",)
    assert check_claims(packet(), (replace(c, value="不支持"),) * 3, load_sources(ROOT)).status == "unknown"


def test_two_current_eligible_opposite_facts_preserve_conflict():
    from chapter18.evidence import check_claims
    p = packet(input_refs=("retention",), output_requirements=("retention",))
    result = check_claims(p, (claim("conflict-a", "retention", "30天"), claim("conflict-b", "retention", "90天")), load_sources(ROOT))
    assert result.status == "conflict"
    assert result.distinct_sources == ("conflict-a", "conflict-b")


@pytest.mark.parametrize("changes", [{"source_id": "missing"}, {"quote": "不存在的原文"}, {"digest": "0" * 64}, {"version": "v1"}])
def test_nonexistent_or_stale_reference_is_unknown(changes):
    from chapter18.evidence import check_claims
    c = claim()
    bad = replace(c, evidence=(replace(c.evidence[0], **changes),))
    assert check_claims(packet(), (bad,), load_sources(ROOT)).status == "unknown"


def test_permission_is_rechecked_and_rejected_quote_is_not_returned():
    from chapter18.evidence import check_claims, knowledge_tool
    c = claim("restricted-current", "internal_quota", "72")
    p = packet(allowed_sources=frozenset({"restricted-current"}), input_refs=("internal_quota",), output_requirements=("internal_quota",))
    verdict = check_claims(p, (c,), load_sources(ROOT))
    assert verdict.status == "blocked" and verdict.claims == ()
    assert "内部额度" not in str(verdict)
    outcome = knowledge_tool(p, ToolCall("read-1", "knowledge", (("source_id", "restricted-current"), ("key", "internal_quota"))), load_sources(ROOT))
    assert outcome.status == "denied" and "72" not in str(outcome.data)


def test_missing_output_requirement_remains_unknown():
    from chapter18.evidence import check_claims
    verdict = check_claims(packet(output_requirements=("sharing", "support_hours")), (claim(),), load_sources(ROOT))
    assert verdict.status == "unknown" and verdict.missing == ("support_hours",)
