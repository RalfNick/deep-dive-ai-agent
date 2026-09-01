from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

from chapter9.incident_domain.tickets import TicketStore
from chapter9.tool_runtime.contracts import DomainError


STATUS_FIELDS = {"observed_at", "services"}
SERVICE_FIELDS = {
    "error_rate",
    "failed_checkout_ratio",
    "p95_latency_ms",
    "window_minutes",
}
DEPLOYMENT_FIELDS = {"deployed_at", "deployment_id", "service", "version"}


def _require_utc_z(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field_name} must be a UTC timestamp ending in Z")
    return value


def _require_exact_fields(
    payload: Mapping[str, object], expected: set[str], label: str
) -> None:
    actual = set(payload)
    if actual != expected:
        unknown = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise ValueError(f"invalid {label} fields: unknown={unknown}, missing={missing}")


@dataclass(frozen=True, slots=True)
class FixtureRepository:
    observed_at: str
    services: Mapping[str, Mapping[str, object]]
    deployments: tuple[Mapping[str, object], ...]
    runbook_text: str

    @classmethod
    def load(cls, root: Path) -> FixtureRepository:
        fixture_root = root.resolve(strict=True)
        status_path = fixture_root / "service-status.json"
        deployments_path = fixture_root / "recent-deployments.json"
        runbook_path = (fixture_root / "runbooks/payments-current.md").resolve(strict=True)
        if not runbook_path.is_relative_to(fixture_root):
            raise ValueError("runbook path escapes fixture root")

        status = json.loads(status_path.read_text(encoding="utf-8"))
        if not isinstance(status, dict):
            raise ValueError("service-status.json must contain an object")
        _require_exact_fields(status, STATUS_FIELDS, "status snapshot")
        observed_at = _require_utc_z(status["observed_at"], "observed_at")

        raw_services = status["services"]
        if not isinstance(raw_services, dict) or not raw_services:
            raise ValueError("services must be a non-empty object")
        services: dict[str, dict[str, object]] = {}
        for service_name, snapshot in sorted(raw_services.items()):
            if not isinstance(snapshot, dict):
                raise ValueError(f"service snapshot must be an object: {service_name}")
            _require_exact_fields(snapshot, SERVICE_FIELDS, f"service {service_name}")
            services[service_name] = dict(snapshot)

        raw_deployments = json.loads(deployments_path.read_text(encoding="utf-8"))
        if not isinstance(raw_deployments, list):
            raise ValueError("recent-deployments.json must contain an array")
        deployments: list[dict[str, object]] = []
        for item in raw_deployments:
            if not isinstance(item, dict):
                raise ValueError("deployment entry must be an object")
            _require_exact_fields(item, DEPLOYMENT_FIELDS, "deployment")
            _require_utc_z(item["deployed_at"], "deployed_at")
            if item["service"] not in services:
                raise ValueError(f"deployment references unknown service: {item['service']}")
            deployments.append(dict(item))
        expected_order = sorted(
            deployments, key=lambda item: str(item["deployed_at"]), reverse=True
        )
        if deployments != expected_order:
            raise ValueError("deployments must be sorted newest first")

        runbook_text = runbook_path.read_text(encoding="utf-8")
        if not runbook_text.strip():
            raise ValueError("runbook must not be empty")
        return cls(
            observed_at=observed_at,
            services=services,
            deployments=tuple(deployments),
            runbook_text=runbook_text,
        )


class IncidentService:
    def __init__(self, repository: FixtureRepository, tickets: TicketStore) -> None:
        self.repository = repository
        self.tickets = tickets

    def get_service_status(self, service: str, window_minutes: int) -> dict[str, object]:
        snapshot = self.repository.services.get(service)
        if snapshot is None:
            raise DomainError("unknown_service", f"unknown service: {service}")
        fixed_window = snapshot["window_minutes"]
        if window_minutes != fixed_window:
            raise DomainError(
                "unsupported_window",
                "the fixture contains only a five-minute status window",
            )
        return {
            "evidence_id": f"status-{service}-0001",
            "service": service,
            "observed_at": self.repository.observed_at,
            **dict(snapshot),
        }

    def list_recent_deployments(
        self, service: str, since: str
    ) -> list[dict[str, object]]:
        if service not in self.repository.services:
            raise DomainError("unknown_service", f"unknown service: {service}")
        try:
            since_utc = _require_utc_z(since, "since")
        except ValueError as error:
            raise DomainError("invalid_since", str(error)) from error
        return [
            dict(item)
            for item in self.repository.deployments
            if item["service"] == service and str(item["deployed_at"]) >= since_utc
        ]

    def current_runbook(self) -> str:
        return self.repository.runbook_text

    def create_incident_ticket(
        self, *, title: str, severity: str, evidence_ids: tuple[str, ...]
    ) -> dict[str, object]:
        return self.tickets.create(
            title=title,
            severity=severity,
            evidence_ids=evidence_ids,
        )

