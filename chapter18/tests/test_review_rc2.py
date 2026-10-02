"""Reader-facing answers and knowledge provenance regression checks."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from chapter18.tests.helpers import ROOT, fixture_repo, packet
from chapter18.tests.test_evidence import claim


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    from chapter18.experiments import run_all
    root = fixture_repo(tmp_path_factory.mktemp("rc2"))
    return run_all(root=root, workdir=root / "chapter18/.runs/review")


def knowledge_case(report):
    return next(c for g in report["groups"] for c in g["cases"] if c["case_id"] == "kb-verified-answer")


def test_existing_but_unrelated_quote_does_not_support_fact():
    from chapter18.evidence import check_claims
    from chapter18.fixtures import load_sources
    c = claim()
    source = next(s for s in load_sources(ROOT) if s.source_id == "public-current")
    unrelated = replace(c, evidence=(replace(c.evidence[0], quote=source.text.splitlines()[0]),))
    verdict = check_claims(packet(), (unrelated,), load_sources(ROOT))
    assert verdict.status == "unknown"
    assert verdict.claims == ()


def test_root_permission_cannot_substitute_worker_scope(report):
    from chapter18.evidence import check_claims
    from chapter18.fixtures import load_sources
    from chapter18.reporting import build_report, packet_from_json, validate_report
    from chapter18.system import encode
    data = deepcopy(report)
    case = knowledge_case(data)
    c = claim("parallel-product")  # Root can read it; this Worker cannot.
    case["worker_results"][0]["claims"] = [encode(c)]
    root = next(p for p in case["input_proof"]["packets"] if p["parent_id"] is None)
    verdict = check_claims(packet_from_json(root), (c,), load_sources(ROOT))
    case["evidence_verdict"] = encode(verdict)
    case["acceptance"] = [f"source:{ref.source_id}:{ref.digest}" for ref in c.evidence]
    data = build_report(tuple(tuple(g["cases"]) for g in data["groups"]))
    with pytest.raises(ValueError, match="worker.*(scope|context)"):
        validate_report(data)


def test_worker_quote_must_occur_in_actual_sent_context(report):
    from chapter18.fixtures import load_sources
    from chapter18.reporting import validate_report
    data = deepcopy(report)
    context = next(c for c in knowledge_case(data)["input_proof"]["context_digests"] if c["task_id"] == "expert")
    source = next(s for s in load_sources(ROOT) if s.source_id == "public-current")
    context["sent"][0][1] = source.text.splitlines()[0]  # Authentic bytes, but no supporting quote.
    context["sent_digest"] = sha256(json.dumps(context["sent"], ensure_ascii=False,
                                               sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with pytest.raises(ValueError, match="worker.*context"):
        validate_report(data)


def test_answer_acceptance_must_reference_its_actual_evidence(report):
    from chapter18.reporting import validate_report
    data = deepcopy(report)
    knowledge_case(data)["acceptance"] = ["source:unrelated:" + "0" * 64]
    with pytest.raises(ValueError, match="answer.*evidence"):
        validate_report(data)


def test_knowledge_quickstart_displays_answer_quotes_and_missing(tmp_path, monkeypatch, capsys):
    from chapter18 import quickstart
    root = fixture_repo(tmp_path)
    monkeypatch.setattr(quickstart, "__file__", str(root / "chapter18/quickstart.py"))
    assert quickstart.main(["--mode", "knowledge", "--workdir", str(root / "chapter18/.runs/reader")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "answer"
    verdict = output["evidence_verdict"]
    assert verdict["missing"] == []
    assert verdict["distinct_sources"] == ["parallel-product", "public-current"]
    assert all(c["value"] == "支持" and c["evidence"][0]["quote"] for c in verdict["claims"])
    assert output["metrics"]["tool_calls"] == 2
