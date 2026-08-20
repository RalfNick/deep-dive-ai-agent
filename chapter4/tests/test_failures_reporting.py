from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.reporting import (  # noqa: E402
    COMPARISON_SCOPE,
    run_boundary_failure_matrix,
    run_fault_case,
    write_boundary_failure_matrix,
)


class FailureAndReportingTest(unittest.TestCase):
    def test_transient_error_retries_once_but_permanent_error_does_not(self) -> None:
        transient = run_fault_case("transient_once")
        permanent = run_fault_case("permanent")

        self.assertEqual(2, transient.attempts)
        self.assertEqual("waiting_approval", transient.status)
        self.assertEqual(1, permanent.attempts)
        self.assertEqual("failed", permanent.status)
        self.assertEqual("permanent_error", permanent.failure_code)

    def test_timeout_cancel_and_step_budget_have_distinct_states(self) -> None:
        timeout = run_fault_case("timeout_once")
        cancelled = run_fault_case("cancelled")
        budget = run_fault_case("step_budget")

        self.assertEqual("waiting_approval", timeout.status)
        self.assertEqual(2, timeout.attempts)
        self.assertEqual("cancelled", cancelled.status)
        self.assertEqual("approval_rejected", cancelled.failure_code)
        self.assertEqual("stopped", budget.status)
        self.assertEqual("max_steps", budget.failure_code)

    def test_boundary_matrix_reports_single_case_observations(self) -> None:
        """Changing observations back to rates would imply nonexistent samples."""
        report = run_boundary_failure_matrix()

        self.assertEqual(COMPARISON_SCOPE, report.comparison_scope)
        self.assertIs(True, report.cases["reference_run"].accepted)
        self.assertIs(
            True, report.cases["verifier_missing"].false_completed
        )
        self.assertGreater(
            report.cases["policy_missing"].policy_violations, 0
        )
        self.assertGreater(
            report.cases["receipt_missing"].duplicate_side_effects, 0
        )
        self.assertIs(
            False,
            report.cases["checkpoint_missing"].recovery_succeeded,
        )
        self.assertIs(
            False,
            report.cases["trace_evidence_lost"].trace_contract_passed,
        )
        self.assertTrue(
            all(case.sample_count == 1 for case in report.cases.values())
        )

    def test_inapplicable_boundary_observations_are_not_fabricated(self) -> None:
        report = run_boundary_failure_matrix()

        self.assertIsNone(report.cases["policy_missing"].accepted)
        self.assertIsNone(
            report.cases["checkpoint_missing"].policy_violations
        )
        self.assertIsNone(
            report.cases["receipt_missing"].recovery_succeeded
        )

    def test_matrix_json_preserves_scope_and_each_observation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="chapter4-report-") as raw:
            path = Path(raw) / "boundary-matrix.json"
            write_boundary_failure_matrix(
                path, run_boundary_failure_matrix()
            )
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(COMPARISON_SCOPE, payload["comparison_scope"])
        self.assertEqual(
            {
                "accepted",
                "false_completed",
                "policy_violations",
                "duplicate_side_effects",
                "recovery_succeeded",
                "trace_contract_passed",
                "steps",
                "simulated_cost_units",
                "sample_count",
            },
            set(payload["cases"]["reference_run"]),
        )


if __name__ == "__main__":
    unittest.main()
