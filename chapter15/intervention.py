"""Evidence-first intervention routing for the Chapter 15 teaching lab."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chapter15.contracts import (
    FailureObservation,
    InterventionDecision,
    InterventionKind,
)


DEFAULT_FAILURE_CASES = Path(__file__).parent / "fixtures" / "failure-cases.json"


def load_failure_cases(path: Path | None = None) -> tuple[FailureObservation, ...]:
    """Load deterministic failure evidence without consulting a model or network."""

    source = DEFAULT_FAILURE_CASES if path is None else Path(path)
    payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    observations: list[FailureObservation] = []
    for item in payload["cases"]:
        observations.append(
            FailureObservation(
                observation_id=item["observation_id"],
                task_id=item["task_id"],
                symptom=item["symptom"],
                repeated_across_tasks=item["repeated_across_tasks"],
                missing_facts=item["missing_facts"],
                deterministic_boundary_available=item["deterministic_boundary_available"],
                instruction_ambiguous=item["instruction_ambiguous"],
                model_capacity_evidence=item["model_capacity_evidence"],
                reusable_supervision=item["reusable_supervision"],
                counterfactual_checks=tuple(item["counterfactual_checks"]),
                evidence_refs=tuple(item["evidence_refs"]),
            )
        )
    return tuple(observations)


def _confidence(observation: FailureObservation, *, decisive: bool) -> str:
    """Classify evidence completeness; this is not a probability estimate."""

    if not decisive:
        return "low"
    if len(observation.evidence_refs) >= 2 and observation.counterfactual_checks:
        return "high"
    return "medium"


def _decision(
    observation: FailureObservation,
    recommended: InterventionKind,
    reason_codes: tuple[str, ...],
    alternatives: tuple[InterventionKind, ...],
    *,
    decisive: bool,
) -> InterventionDecision:
    return InterventionDecision(
        recommended=recommended,
        reason_codes=reason_codes,
        evidence_refs=observation.evidence_refs,
        alternatives=alternatives,
        confidence=_confidence(observation, decisive=decisive),
    )


def recommend_intervention(observation: FailureObservation) -> InterventionDecision:
    """Choose the smallest intervention supported by counterfactual evidence.

    Post-training is deliberately a fallback.  It becomes eligible only when
    four upstream explanations have been ruled out, the failure repeats across
    tasks, and the trace set contains reusable supervision.
    """

    direct_signals: list[tuple[InterventionKind, str]] = []
    if observation.missing_facts:
        direct_signals.append((InterventionKind.RAG_CONTEXT, "missing_facts_confirmed"))
    if observation.deterministic_boundary_available:
        direct_signals.append((InterventionKind.HARNESS, "deterministic_boundary_available"))
    if observation.instruction_ambiguous:
        direct_signals.append((InterventionKind.PROMPT_SKILL, "instruction_ambiguity_unresolved"))
    if observation.model_capacity_evidence:
        direct_signals.append((InterventionKind.MODEL_ROUTE, "model_capacity_gap_verified"))

    if len(direct_signals) > 1:
        return _decision(
            observation,
            InterventionKind.INCONCLUSIVE,
            ("conflicting_intervention_evidence",),
            tuple(kind for kind, _ in direct_signals),
            decisive=False,
        )

    if len(direct_signals) == 1:
        recommended, reason = direct_signals[0]
        return _decision(
            observation,
            recommended,
            (reason,),
            (InterventionKind.POST_TRAINING,),
            decisive=True,
        )

    counterfactuals_exhausted = len(observation.counterfactual_checks) >= 3
    evidence_is_repeated = len(observation.evidence_refs) >= 2
    if (
        observation.repeated_across_tasks
        and observation.reusable_supervision
        and counterfactuals_exhausted
        and evidence_is_repeated
    ):
        return _decision(
            observation,
            InterventionKind.POST_TRAINING,
            (
                "policy_bias_repeats_across_tasks",
                "reusable_supervision_available",
                "counterfactuals_exhausted",
            ),
            (InterventionKind.PROMPT_SKILL, InterventionKind.MODEL_ROUTE),
            decisive=True,
        )

    return _decision(
        observation,
        InterventionKind.INCONCLUSIVE,
        ("insufficient_post_training_evidence",),
        (
            InterventionKind.RAG_CONTEXT,
            InterventionKind.HARNESS,
            InterventionKind.PROMPT_SKILL,
            InterventionKind.MODEL_ROUTE,
        ),
        decisive=False,
    )
