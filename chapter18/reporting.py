from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path

from .contracts import BudgetLimits, Claim, EvidenceRef, TaskPacket, TeamReport, relative_path, validate_packet
from .evidence import check_claims
from .fixtures import load_case_specs, load_sources
from .system import derive_metrics, encode

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"answer", "verified", "unknown", "blocked", "conflict", "needs_approval", "stopped"}


def build_report(groups) -> TeamReport:
    rows = []
    for number, cases in enumerate(groups, 1):
        normalized = []
        for original in cases:
            case = deepcopy(original)
            case["metrics"] = derive_metrics(case)
            normalized.append(case)
        rows.append({"group": number, "cases": normalized})
    flat = [c for row in rows for c in row["cases"]]
    metrics = {key: sum(c["metrics"][key] for c in flat) for key in flat[0]["metrics"]} if flat else {}
    metrics.update(cases_total=len(flat), status_counts=dict(sorted(Counter(c["status"] for c in flat).items())))
    return {"schema_version": "chapter18.team.v1", "groups": rows, "summary": metrics,
            "limits": ["Twenty deterministic teaching cases; no model ranking.", "Logical scheduling is not measured latency or cost.",
                       "Directory/context checks are not an operating-system sandbox.", "Source byte matching and explicit fixture facts are not general semantic entailment."]}


def packet_from_json(row) -> TaskPacket:
    values = dict(row)
    values["limits"] = BudgetLimits(**values["limits"])
    for key in ("allowed_sources", "allowed_tools", "allowed_writes"):
        values[key] = frozenset(values[key])
    for key in ("input_refs", "output_requirements"):
        values[key] = tuple(values[key])
    values["base_hashes"] = tuple(tuple(pair) for pair in values["base_hashes"])
    return TaskPacket(**values)


def validate_case(case) -> None:
    if "single_controller_control" in case:
        validate_case(case["single_controller_control"])
        control = case["single_controller_control"]
        if control["evidence_verdict"] != case["evidence_verdict"] or control["metrics"]["coverage_denominator"] != case["metrics"]["coverage_denominator"]:
            raise ValueError("comparison must preserve target and evidence")
    if case["status"] not in STATUSES:
        raise ValueError("invalid final status")
    metrics = derive_metrics(case)
    if case["metrics"] != metrics or any(type(v) is not int or v < 0 for v in metrics.values()):
        raise ValueError("metrics must come from actual trajectory")
    if metrics["coverage_numerator"] > metrics["coverage_denominator"]:
        raise ValueError("coverage exceeds requested goals")
    packets = {p["task_id"]: packet_from_json(p) for p in case["input_proof"]["packets"]}
    if len(packets) != len(case["input_proof"]["packets"]):
        raise ValueError("duplicate task")
    roots = [p for p in packets.values() if p.parent_id is None]
    if len(roots) != 1:
        raise ValueError("one root required")
    root_packet = roots[0]
    for p in packets.values():
        parent = packets.get(p.parent_id) if p.parent_id else None
        if p.parent_id and parent is None:
            raise ValueError("missing parent task")
        validate_packet(p, parent)
    limits = root_packet.limits
    if metrics["tool_calls"] > limits.tool_calls or metrics["verifier_calls"] > limits.verifier_reserve:
        raise ValueError("global budget exceeded")
    if metrics["tool_calls"] - metrics["verifier_calls"] > limits.tool_calls - limits.verifier_reserve:
        raise ValueError("worker spent verifier reserve")
    events = {e["event_id"]: e for e in case["trajectory"]}
    if len(events) != len(case["trajectory"]):
        raise ValueError("duplicate event")
    attempts = case["input_proof"]["attempts"]
    if set(attempts) != set(packets):
        raise ValueError("each task needs exactly one attempt")
    sources = {s.source_id: s for s in load_sources(ROOT)}
    for event in events.values():
        if event["task_id"] not in packets or event["attempt_id"] != attempts[event["task_id"]]:
            raise ValueError("event task/attempt mismatch")
        parent = event["parent_event_id"]
        if parent is not None and (parent not in events or events[parent]["task_id"] != event["task_id"]
                                  or int(parent.rsplit(":e", 1)[1]) >= int(event["event_id"].rsplit(":e", 1)[1])):
            raise ValueError("invalid causal predecessor")
    for p in packets.values():
        starts = [e for e in events.values() if e["task_id"] == p.task_id and e["kind"] == "task_started"]
        if len(starts) != 1 or starts[0]["data"] != {"worker": p.worker_id, "parent": p.parent_id}:
            raise ValueError("task start evidence missing or mismatched")
    source_proof = set()
    for context in case["input_proof"]["context_digests"]:
        p = packets[context["task_id"]]
        if (context["principal"], context["target_version"]) != (p.principal, p.target_version):
            raise ValueError("context scope mismatch")
        digest = sha256(json.dumps(context["sent"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if not context.get("redacted", False) and digest != context["sent_digest"]:
            raise ValueError("sent context digest mismatch")
        if context.get("redacted", False) and case["status"] == "answer":
            raise ValueError("revoked context cannot authorize final answer")
        for source_id, claimed_digest in context["source_digests"]:
            if source_id.startswith("src/"):
                relative_path(source_id)
                if source_id not in p.allowed_writes:
                    raise ValueError("code context outside scope")
                data = (ROOT / "chapter18/fixtures/link-checker" / source_id).read_bytes()
                actual_digest = sha256(data).hexdigest()
            elif source_id in sources and source_id in p.allowed_sources:
                actual_digest = sources[source_id].digest
            else:
                raise ValueError("unknown context source")
            if claimed_digest != actual_digest:
                raise ValueError("original source digest mismatch")
            source_proof.add((source_id, claimed_digest))
        for source_id, text in context["sent"]:
            if source_id.startswith("src/"):
                if source_id not in p.allowed_writes or text != (ROOT / "chapter18/fixtures/link-checker" / source_id).read_text(encoding="utf-8"):
                    raise ValueError("code context content mismatch")
            else:
                doc = sources.get(source_id)
                if (doc is None or source_id not in p.allowed_sources or p.principal not in doc.principals
                        or any(line not in doc.text for line in text.splitlines())):
                    raise ValueError("sent fragment cannot be tied to source")
    if set(tuple(pair) for pair in case["input_proof"]["source_digests"]) != source_proof:
        raise ValueError("aggregated original source proof mismatch")
    claims = []
    seen_results = set()
    for result in case["worker_results"]:
        p = packets[result["task_id"]]
        if result["worker_id"] != p.worker_id or result["attempt_id"] != attempts[p.task_id] or p.task_id in seen_results:
            raise ValueError("worker result identity mismatch")
        seen_results.add(p.task_id)
        accepted = [e for e in events.values() if e["kind"] == "result_accepted" and e["task_id"] == p.task_id]
        if len(accepted) != 1 or accepted[0]["data"]["worker_state"] != result["state"]:
            raise ValueError("accepted worker result needs its acceptance event")
        actual_decisions = sum(e["kind"] == "decision" and e["task_id"] == p.task_id for e in events.values())
        actual_calls = sum(e["kind"] == "tool_returned" and e["task_id"] == p.task_id for e in events.values())
        if (result["decisions"], result["tool_calls"]) != (actual_decisions, actual_calls):
            raise ValueError("worker counters must match events")
        for row in result["claims"]:
            claims.append(Claim(row["key"], row["value"], tuple(EvidenceRef(**ref) for ref in row["evidence"])))
    if {e["task_id"] for e in events.values() if e["kind"] == "result_accepted"} != seen_results:
        raise ValueError("acceptance events and exported results disagree")
    committed = [e for e in events.values() if e["kind"] == "action_committed"]
    executed = [r for r in case["receipts"] if r["executed"]]
    if len(committed) != len(executed) or len({r["action_id"] for r in executed}) != len(executed):
        raise ValueError("every executed receipt needs one unique commit event")
    for receipt in executed:
        matches = [e for e in committed if e["data"]["action_id"] == receipt["action_id"]]
        if len(matches) != 1:
            raise ValueError("commit/receipt identity mismatch")
        event = matches[0]
        d = event["data"]
        owner = packets.get(d.get("proposal_task_id"))
        accepted_owner = next((r for r in case["worker_results"] if owner and r["task_id"] == owner.task_id), None)
        if (event["task_id"] != root_packet.task_id or owner is None or accepted_owner is None
                or d.get("proposal_attempt_id") != attempts[owner.task_id] or d.get("proposal_worker") != owner.worker_id
                or receipt["proposal_id"] not in accepted_owner["patch_ids"]
                or d.get("proposal_id") != receipt["proposal_id"]
                or any(d.get(key) != receipt[key] for key in ("path", "before_digest", "after_digest"))
                or receipt["path"] not in owner.allowed_writes or receipt["path"] not in root_packet.allowed_writes
                or dict(owner.base_hashes).get(receipt["path"]) != receipt["before_digest"]):
            raise ValueError("commit must correlate accepted producer, scope and before/after digests")
    verification_events = [e for e in events.values() if e["kind"] == "verification"]
    verified_receipts = [r for r in executed if r["verification"] is not None]
    if bool(verification_events) != bool(verified_receipts) or len(verification_events) > 1:
        raise ValueError("final verification and receipt evidence must both exist")
    if verified_receipts:
        v = verified_receipts[0]["verification"]
        expected_event = {key: v[key] for key in ("tests_passed", "tests_total", "behavior_passed", "passed")}
        expected_event.update(calls=2 if v["passed"] else metrics["verifier_calls"],
                              evidence_digest=sha256("\n".join(v["evidence"]).encode()).hexdigest())
        if (any(r["verification"] != v for r in verified_receipts)
                or len(verified_receipts) != len(executed) or verification_events[0]["task_id"] != root_packet.task_id
                or verification_events[0]["data"] != expected_event or v["evidence"] != case["acceptance"]):
            raise ValueError("final verification event, calls and receipts must correlate")
    # Tightened child allowance counts its whole subtree, including retries and real commits.
    for p in packets.values():
        if p.parent_id is None:
            continue
        descendants = set()
        for other in packets.values():
            cursor = other
            while cursor:
                if cursor.task_id == p.task_id:
                    descendants.add(other.task_id)
                    break
                cursor = packets.get(cursor.parent_id)
        spent = sum(e["kind"] == "tool_returned" and e["task_id"] in descendants for e in events.values())
        spent += sum(e["data"]["proposal_task_id"] in descendants for e in committed)
        if spent > p.limits.tool_calls - p.limits.verifier_reserve:
            raise ValueError("child subtree spent tightened worker quota")
    verdict = check_claims(root_packet, tuple(claims), load_sources(ROOT))
    if encode(verdict) != case["evidence_verdict"]:
        raise ValueError("evidence verdict cannot be forged")
    if case["status"] == "answer" and (verdict.status != "answer" or not case["acceptance"]):
        raise ValueError("answer requires current eligible evidence")
    if case["status"] == "verified":
        executed = [r for r in case["receipts"] if r["executed"]]
        if not executed or metrics["security_violations"] or not case["acceptance"]:
            raise ValueError("verified requires authorized execution and evidence")
        patch_ids = {pid for r in case["worker_results"] for pid in r["patch_ids"]}
        for receipt in executed:
            v = receipt["verification"]
            if receipt["proposal_id"] not in patch_ids or not v or not (v["passed"] and v["tests_passed"] == v["tests_total"] == 4 and v["behavior_passed"]):
                raise ValueError("verified requires accepted proposal and independent checks")
            if v["evidence"] != case["acceptance"]:
                raise ValueError("acceptance and receipt evidence disagree")


def validate_report(report: TeamReport) -> None:
    try:
        if report["schema_version"] != "chapter18.team.v1" or [g["group"] for g in report["groups"]] != list(range(1, 6)):
            raise ValueError("five ordered groups required")
        expected = {(row["case_id"], row["group"]) for row in load_case_specs(ROOT)}
        cases = [c for g in report["groups"] for c in g["cases"]]
        if len(cases) != 20 or {(c["case_id"], c["group"]) for c in cases} != expected:
            raise ValueError("twenty unique declared cases required")
        for group in report["groups"]:
            if len(group["cases"]) != 4 or any(c["group"] != group["group"] for c in group["cases"]):
                raise ValueError("case/group mismatch")
            for case in group["cases"]:
                validate_case(case)
        expected_summary = build_report(tuple(tuple(g["cases"]) for g in report["groups"]))["summary"]
        if report["summary"] != expected_summary:
            raise ValueError("summary must be derived")
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("malformed evidence report") from error


def validate_exercises(payload) -> None:
    if payload.get("schema_version") != "chapter18.exercises.v1" or [a["exercise_id"] for a in payload["answers"]] != list(range(1, 14)):
        raise ValueError("thirteen ordered answers required")
    refs = set()
    for row in payload["case_evidence"]:
        prefix = "case:" + row["case_id"]
        refs.add(prefix)
        refs.update(prefix + "/event:" + eid for eid in row["event_ids"])
    if any(ref not in refs for answer in payload["answers"] for ref in answer["evidence_refs"]):
        raise ValueError("exercise evidence reference missing")
