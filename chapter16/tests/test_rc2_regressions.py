"""Reader-review failures reproduced through the ordinary public entry points."""
from dataclasses import replace

import pytest

from chapter16.contracts import CLOCK, END, ReleaseRecord, ReleaseState
from chapter16.artifacts import build_candidate
from chapter16.evaluation import decide_gate, evaluate_pair, make_context
from chapter16.experiments import prepare
from chapter16.governance import activate, make_approval, rollback
from chapter16.feedback import admit_feedback
from chapter16.lessons import propose_lessons
from chapter16.replay import attribute, replay
from chapter16.serialization import body_hash


def approve(candidate, evidence):
    return make_approval(candidate, evidence, approver_id="reviewer-local",
                         allowed_scopes=tuple(a.scope for a in candidate.artifacts),
                         now=CLOCK, valid_until=END)


def active_release(lab):
    _, _, baseline, candidate, _, context, evidence = prepare(lab)
    state = activate(ReleaseState(baseline, (), frozenset()), candidate, evidence,
                     approve(candidate, evidence), context, now=CLOCK)
    return state, baseline, candidate


def test_rollback_cannot_restore_a_revision_that_was_rolled_back(lab):
    active, baseline, candidate = active_release(lab)
    back = rollback(active, baseline, reason="observed_fault", now="2026-09-28T00:01:00Z")
    with pytest.raises(ValueError, match="fresh.*validation"):
        rollback(back, candidate, reason="restore_known_revision", now="2026-09-28T00:02:00Z")
    assert back.active == baseline and len(back.history) == 2


def test_rollback_cannot_be_dated_before_its_release_history(lab):
    active, baseline, _ = active_release(lab)
    with pytest.raises(ValueError, match="clock"):
        rollback(active, baseline, reason="clock_reversal", now="2026-09-27T23:59:59Z")


def test_stopped_active_revision_cannot_be_restored_by_noop_rollback(lab):
    active, _, candidate = active_release(lab)
    stopped_at = "2026-09-28T00:01:00Z"
    stop = ReleaseRecord("pending", "stop", candidate, candidate, None, None, {}, "observed_fault", stopped_at)
    stop = replace(stop, record_id=body_hash(stop, "record_id"))
    stopped = replace(active, history=active.history + (stop,))
    with pytest.raises(ValueError, match="fresh.*validation"):
        rollback(stopped, candidate, reason="restore_stopped", now="2026-09-28T00:02:00Z")


def test_old_activation_is_not_an_idempotent_retry_after_a_stop(lab):
    _, _, baseline, candidate, _, context, evidence = prepare(lab)
    approval = approve(candidate, evidence)
    active = activate(ReleaseState(baseline, (), frozenset()), candidate, evidence, approval, context, now=CLOCK)
    stop = ReleaseRecord("pending", "stop", candidate, candidate, None, None, {}, "observed_fault",
                         "2026-09-28T00:01:00Z")
    stop = replace(stop, record_id=body_hash(stop, "record_id"))
    stopped = replace(active, history=active.history + (stop,))
    with pytest.raises(ValueError, match="stopped"):
        activate(stopped, candidate, evidence, approval, context, now="2026-09-28T00:02:00Z")


@pytest.mark.parametrize("ref,payload", [
    ("F08", {"answer_style":"normal"}),
    ("F01", {"selection":"scoped_current", "document_id":"A-old"}),
    ("F03", {"steps":["open_project", "open_data", "export"]}),
    ("F01", {"selection":"scoped_current"}),
])
def test_authority_and_key_presence_do_not_authorize_contradictory_asset_content(
        lab, baseline, candidate, use_policy, ref, payload):
    changed = replace(lab, feedback=tuple(replace(f, payload=payload) if f.feedback_id == ref else f
                                         for f in lab.feedback))
    evidence = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate,
                             make_context(changed, use_policy))
    # Runtime and hidden graders still score every task correctly. Provenance must veto separately.
    assert all(r["candidate_grade"]["status"] == "pass" for r in evidence.paired_trials)
    proof = next(p for p in evidence.asset_evidence if p.source_ref == ref)
    assert proof.status == "fail" and proof.reason_codes == ("source_content_mismatch",)
    assert decide_gate(evidence).status == "fail"
    with pytest.raises(ValueError):
        approve(candidate, evidence)


def test_additional_non_behavioral_source_text_does_not_require_verbatim_asset_copy(
        lab, baseline, candidate, use_policy):
    changed = replace(lab, feedback=tuple(
        replace(f, payload={**f.payload, "explanation":"The entry moved to the data page."})
        if f.feedback_id == "F01" else f for f in lab.feedback))
    evidence = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate,
                             make_context(changed, use_policy))
    assert decide_gate(evidence).status == "pass"


def replay_without_current_document(lab):
    return replace(lab, replays=tuple(
        replace(c, documents=tuple(d for d in c.documents if d.document_id != "A-current"))
        if c.case_id == "F01" else c for c in lab.replays))


def test_removing_target_document_is_unknown_not_a_successful_selection_intervention(lab):
    changed = replay_without_current_document(lab)
    case = next(c for c in changed.replays if c.case_id == "F01")
    assert replay(case).outcome.document_id == "A-old"
    selected = replay(case, selection="scoped_current")
    assert selected.status == "unknown"
    assert "no_authorized_document" in selected.missing
    attribution = attribute(case)
    assert attribution.cause == "unknown"
    assert "no_authorized_document" in attribution.unknown_reasons
    proposals = propose_lessons(admit_feedback(changed.feedback, changed.sources), changed.replays,
                                blocked_families=frozenset())
    proposal = next(p for p in proposals if p.source_refs == ("F01",))
    assert proposal.unknown_reasons
    with pytest.raises(ValueError, match="unresolved"):
        build_candidate(proposals, now=CLOCK)


def test_old_candidate_cannot_pass_provenance_when_only_its_discovery_document_disappears(
        lab, baseline, candidate, use_policy):
    changed = replay_without_current_document(lab)
    evidence = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate,
                             make_context(changed, use_policy))
    assert all(r["candidate_grade"]["status"] == "pass" for r in evidence.paired_trials)
    assert next(p for p in evidence.asset_evidence if p.source_ref == "F01").status == "unknown"
    assert decide_gate(evidence).status == "inconclusive"
    with pytest.raises(ValueError):
        approve(candidate, evidence)


def test_changed_steps_require_positive_source_condition_not_merely_different_output(
        lab, baseline, candidate, use_policy):
    changed = replace(lab, replays=tuple(
        replace(c, documents=tuple(replace(d, steps=("open_project", "verify_receipt"))
                                   if d.document_id == "A-steps" else d for d in c.documents))
        if c.case_id == "F03" else c for c in lab.replays))
    evidence = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate,
                             make_context(changed, use_policy))
    assert all(r["candidate_grade"]["status"] == "pass" for r in evidence.paired_trials)
    proof = next(p for p in evidence.asset_evidence if p.source_ref == "F03")
    assert proof.status == "unknown"
    assert decide_gate(evidence).status == "inconclusive"
    proposals = propose_lessons(admit_feedback(changed.feedback, changed.sources), changed.replays,
                                blocked_families=frozenset())
    proposal = next(p for p in proposals if p.source_refs == ("F03",))
    assert proposal.unknown_reasons == ("discovery_condition_not_verified",)
    with pytest.raises(ValueError, match="unresolved"):
        build_candidate(proposals, now=CLOCK)


def test_different_current_document_is_not_proof_of_the_source_required_document(
        lab, baseline, candidate, use_policy):
    changed = replace(lab, replays=tuple(
        replace(c, documents=tuple(replace(d, document_id="A-alternate-current")
                                   if d.document_id == "A-current" else d for d in c.documents))
        if c.case_id == "F01" else c for c in lab.replays))
    evidence = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate,
                             make_context(changed, use_policy))
    assert all(r["candidate_grade"]["status"] == "pass" for r in evidence.paired_trials)
    assert next(p for p in evidence.asset_evidence if p.source_ref == "F01").status == "unknown"
    assert decide_gate(evidence).status == "inconclusive"
    proposals = propose_lessons(admit_feedback(changed.feedback, changed.sources), changed.replays,
                                blocked_families=frozenset())
    assert next(p for p in proposals if p.source_refs == ("F01",)).unknown_reasons == ("discovery_condition_not_verified",)


def test_exercise_solutions_recompute_new_discovery_provenance_and_restore_boundaries():
    from chapter16.exercise_solutions import solve
    assert solve(5)["evidence"]["F01"]["verified_discovery"] is True
    assert solve(5)["evidence"]["F03"]["verified_discovery"] is True
    assert solve(10)["evidence"]["unsupported_source"] == "fail"
    assert solve(11)["evidence"]["stopped_restore_rejected"] is True
    assert solve(9)["evidence"]["unused_old_evidence_rejected"] is True


@pytest.mark.parametrize("frozen_clock", [CLOCK, "2026-09-28T00:02:00Z"])
def test_unused_evidence_precomputed_before_rollback_is_not_fresh_validation(lab, frozen_clock):
    _, _, baseline, candidate, policy, context, original = prepare(lab)
    saved_context = make_context(lab, policy, frozen_clock=frozen_clock,
                                 valid_until="2026-09-28T12:00:00Z")
    saved = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, saved_context)
    assert saved.evidence_hash != original.evidence_hash and decide_gate(saved).status == "pass"
    active = activate(ReleaseState(baseline, (), frozenset()), candidate, original,
                      approve(candidate, original), context, now=CLOCK)
    back = rollback(active, baseline, reason="observed_fault", now="2026-09-28T00:01:00Z")
    approval = make_approval(candidate, saved, approver_id="reviewer-local",
                             allowed_scopes=tuple(a.scope for a in candidate.artifacts),
                             now="2026-09-28T00:02:00Z", valid_until=saved_context.valid_until)
    with pytest.raises(ValueError, match="fresh.*validation"):
        activate(back, candidate, saved, approval, saved_context, now="2026-09-28T00:02:00Z")


def test_notes_remain_in_admissions_but_not_in_executable_asset_content(lab):
    changed = replace(lab, feedback=tuple(
        replace(f, payload={**f.payload, "explanation":"The entry moved to the data page."})
        if f.feedback_id == "F01" else f for f in lab.feedback))
    admissions, proposals, _, candidate, _, _, evidence = prepare(changed)
    assert next(a for a in admissions if a.feedback_id == "F01").sanitized_payload["explanation"]
    proposal = next(p for p in proposals if p.source_refs == ("F01",))
    assert set(proposal.content) == {"selection", "document_id"}
    assert all("explanation" not in a.content for a in candidate.artifacts)
    assert decide_gate(evidence).status == "pass"


def test_stop_entry_records_control_event_and_requires_later_actual_validation(lab):
    from chapter16.governance import stop
    _, _, baseline, candidate, policy, context, evidence = prepare(lab)
    # Save a future-labelled evaluation before the stop. A later clock label is not an issuance receipt.
    late_context = make_context(lab, policy, frozen_clock="2026-09-28T00:03:00Z")
    saved = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, late_context)
    active = activate(ReleaseState(baseline, (), frozenset()), candidate, evidence,
                      approve(candidate, evidence), context, now=CLOCK)
    stopped = stop(active, reason="observed_fault", now="2026-09-28T00:01:00Z")
    assert stopped.active == candidate and [r.event for r in stopped.history] == ["activate", "stop"]
    back = rollback(stopped, baseline, reason="recover_baseline", now="2026-09-28T00:02:00Z")
    approval = make_approval(candidate, saved, approver_id="reviewer-local",
                             allowed_scopes=tuple(a.scope for a in candidate.artifacts),
                             now="2026-09-28T00:03:00Z", valid_until=END)
    with pytest.raises(ValueError, match="fresh.*validation"):
        activate(back, candidate, saved, approval, late_context, now="2026-09-28T00:03:00Z")
    fresh = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, late_context)
    # Same frozen material as the unused saved result, but really evaluated after both stop events.
    assert fresh.evidence_hash == saved.evidence_hash
    new_approval = make_approval(candidate, fresh, approver_id="reviewer-local",
                                 allowed_scopes=tuple(a.scope for a in candidate.artifacts),
                                 now="2026-09-28T00:03:00Z", valid_until=END)
    restored = activate(back, candidate, fresh, new_approval, late_context, now="2026-09-28T00:03:00Z")
    assert restored.active == candidate and [r.event for r in restored.history] == ["activate", "stop", "rollback", "activate"]
    assert activate(restored, candidate, fresh, new_approval, late_context, now="2026-09-28T00:03:00Z") is restored


def test_precomputed_alternate_revision_also_requires_validation_after_release_interruption(lab):
    from chapter16.artifacts import make_snapshot
    _, _, baseline, candidate, policy, context, original = prepare(lab)
    alternate = make_snapshot(candidate.artifacts, revision_id="candidate-precomputed-v2")
    saved_context = make_context(lab, policy, frozen_clock="2026-09-28T00:02:00Z")
    saved = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, alternate, saved_context)
    active = activate(ReleaseState(baseline, (), frozenset()), candidate, original,
                      approve(candidate, original), context, now=CLOCK)
    back = rollback(active, baseline, reason="observed_fault", now="2026-09-28T00:01:00Z")
    approval = make_approval(alternate, saved, approver_id="reviewer-local",
                             allowed_scopes=tuple(a.scope for a in alternate.artifacts),
                             now="2026-09-28T00:02:00Z", valid_until=END)
    with pytest.raises(ValueError, match="fresh.*validation"):
        activate(back, alternate, saved, approval, saved_context, now="2026-09-28T00:02:00Z")
