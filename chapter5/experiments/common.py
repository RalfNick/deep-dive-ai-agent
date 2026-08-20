from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from typing import Sequence

from chapter4.harness.gateway import ActionGateway

from ..context.builder import ContextBuilder
from ..context.contracts import BuildConfig, DecisionKind, ProbeStatus
from ..context.serialization import PacketSerializer
from ..fixtures.canonical import FixtureSource, materialize
from ..gateway_adapter import GatewayObservation, evaluate_proposal
from ..graders import (
    BuildGrader,
    CaseRecord,
    DecisionGrader,
    SafetyGrader,
)
from ..probes import ModelProbe, RuleBasedProbe


@dataclass(frozen=True)
class CaseDefinition:
    experiment: str
    variant: str
    sources: tuple[FixtureSource, ...]
    config: BuildConfig
    expected_kind: DecisionKind
    expected_tool: str | None
    required_arguments: frozenset[str]
    irrelevant_source_ids: frozenset[str]
    supported_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    expected_selected_item_ids: frozenset[str] = frozenset()
    expected_trace_reasons: tuple[tuple[str, str], ...] = ()


def run_case(
    case: CaseDefinition,
    *,
    probe: ModelProbe | None = None,
    live: bool = False,
) -> CaseRecord:
    items = materialize(case.sources)
    item_by_source = {item.provenance.source_id: item for item in items}
    build = ContextBuilder().build(items, case.config)
    active_probe = probe or RuleBasedProbe()
    probe_run = active_probe.probe(build.packet)
    gateway_observation: GatewayObservation | None = None
    if (
        probe_run.status is ProbeStatus.OK
        and probe_run.decision is not None
        and probe_run.decision.kind is DecisionKind.TOOL
    ):
        gateway_observation = evaluate_proposal(
            probe_run.decision,
            run_id=f"{case.experiment}-{case.variant}",
            ordinal=1,
            gateway=ActionGateway(),
        )

    irrelevant_ids = frozenset(
        item_by_source[source_id].item_id
        for source_id in case.irrelevant_source_ids
        if source_id in item_by_source
    )
    build_grade = BuildGrader().grade(
        build,
        expected_requirements=case.config.expected_requirements,
        candidate_item_ids=frozenset(item.item_id for item in items),
        irrelevant_item_ids=irrelevant_ids,
        expected_selected_item_ids=case.expected_selected_item_ids,
        expected_trace_reasons=dict(case.expected_trace_reasons),
    )
    decision_grade = DecisionGrader().grade(
        probe_run,
        expected_kind=case.expected_kind,
        expected_tool=case.expected_tool,
        required_arguments=case.required_arguments,
    )
    provider_payload = "\n".join(
        message["content"]
        for message in PacketSerializer().to_messages(build.packet)
    )
    trace_payload = json.dumps(asdict(build.trace), ensure_ascii=False, default=str)
    secret_values = tuple(
        source.raw.content for source in case.sources if source.raw.channel == "secret_fixture"
    )
    hostile_item_ids = tuple(
        item.item_id
        for source, item in zip(case.sources, items, strict=True)
        if source.raw.channel == "hostile_fixture"
    )
    safety_grade = SafetyGrader().grade(
        probe_run=probe_run,
        gateway_observation=gateway_observation,
        provider_payload=provider_payload,
        trace_payload=trace_payload,
        secret_values=secret_values,
        hostile_item_ids=hostile_item_ids,
    )
    valid = int(probe_run.status is ProbeStatus.OK and decision_grade is not None)
    return CaseRecord(
        experiment=case.experiment,
        variant=case.variant,
        probe_type=probe_run.requested_model,
        probe_status=probe_run.status,
        task_outcome=decision_grade.outcome if decision_grade is not None else None,
        semantic_packet_digest=build.packet.semantic_packet_digest,
        provider_request_digest=probe_run.request_digest if live else None,
        selected_item_ids=build.packet.selected_item_ids,
        missing_requirements=build.packet.missing_requirements,
        build_grade=build_grade,
        decision_grade=decision_grade,
        safety_grade=safety_grade,
        gateway_kind=(
            gateway_observation.decision.kind.value
            if gateway_observation is not None
            else None
        ),
        total_attempts=1,
        valid_decisions=valid,
        infrastructure_failure=None if valid else probe_run.status.value,
        supported_claims=case.supported_claims,
        unsupported_claims=case.unsupported_claims,
        returned_model=probe_run.returned_model,
        usage=tuple(sorted(probe_run.usage.items())),
        latency_ms=probe_run.latency_ms,
        retry_count=probe_run.retry_count,
        run_date=date.today().isoformat() if live else None,
    )


def render_records(records: Sequence[CaseRecord]) -> str:
    from ..graders import ExperimentReport

    return ExperimentReport.from_records(records).to_json()
