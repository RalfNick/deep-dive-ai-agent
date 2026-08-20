from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from chapter5.context.contracts import DecisionKind, TaskOutcome
from chapter5.experiments.assembly_ablation import run_assembly_ablation
from chapter5.experiments.information_position import run_information_position
from chapter5.experiments.instruction_conflict import run_instruction_conflict
from chapter5.experiments.noise_and_injection import run_noise_and_injection
from chapter5.experiments.run_all import run_all
from chapter5.experiments.tool_description import run_tool_description


EXPECTED_VARIANTS = {
    "assembly_ablation": {
        "complete",
        "missing_required",
        "duplicate",
        "tight_budget",
        "required_restored",
    },
    "instruction_conflict": {
        "trusted_first",
        "trusted_last",
        "user_vs_repository",
        "observation_vs_instruction",
        "hostile_first",
        "hostile_last",
        "fact_conflict",
    },
    "information_position": {
        "front_t1",
        "middle_t1",
        "back_t1",
        "front_t2",
        "middle_t2",
        "back_t2",
        "front_t3",
        "middle_t3",
        "back_t3",
    },
    "tool_description": {
        "vague",
        "precise",
        "precise_with_negative_constraint",
    },
    "noise_and_injection": {
        "noise_0",
        "noise_5",
        "noise_20",
        "injection_authority",
        "injection_secret",
        "injection_path",
    },
}
REPO_ROOT = Path(__file__).resolve().parents[2]


class ContextExperimentTest(unittest.TestCase):
    def test_live_cli_without_key_writes_config_error_report(self) -> None:
        environment = os.environ.copy()
        environment.pop("DEEPSEEK_API_KEY", None)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "missing-key.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chapter5.experiments.run_all",
                    "--live",
                    "--repeats",
                    "1",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertTrue(output.exists())
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual("config_error", report["run_status"])
        self.assertEqual("missing_credential", report["configuration_error"])
        self.assertEqual("deepseek-v4-pro", report["requested_model"])
        self.assertEqual(0, report["total_attempts"])
        self.assertEqual(0, report["valid_decisions"])
        self.assertEqual([], report["records"])
    def test_each_experiment_has_the_frozen_variant_set(self) -> None:
        groups = {
            "assembly_ablation": run_assembly_ablation(),
            "instruction_conflict": run_instruction_conflict(),
            "information_position": run_information_position(),
            "tool_description": run_tool_description(),
            "noise_and_injection": run_noise_and_injection(),
        }

        for name, records in groups.items():
            with self.subTest(experiment=name):
                self.assertEqual(EXPECTED_VARIANTS[name], {record.variant for record in records})
                self.assertEqual({"rule-based-v1"}, {record.probe_type for record in records})
                self.assertTrue(all(record.supported_claims for record in records))
                self.assertTrue(all(record.unsupported_claims for record in records))

    def test_assembly_missing_required_refuses_to_guess(self) -> None:
        records = {record.variant: record for record in run_assembly_ablation()}

        self.assertEqual(
            TaskOutcome.NEEDS_CONTEXT,
            records["missing_required"].task_outcome,
        )
        self.assertIn("currency-test", records["missing_required"].missing_requirements)
        self.assertEqual(TaskOutcome.CORRECT, records["complete"].task_outcome)

    def test_instruction_conflicts_use_explicit_build_contracts(self) -> None:
        records = {record.variant: record for record in run_instruction_conflict()}

        self.assertTrue(
            all(record.build_grade.conflict_contract_checked for record in records.values())
        )
        self.assertTrue(
            all(record.build_grade.conflict_resolution_correct for record in records.values())
        )
        self.assertIn("user_vs_repository", records)
        self.assertIn("observation_vs_instruction", records)
        self.assertEqual(TaskOutcome.CORRECT, records["user_vs_repository"].task_outcome)
        self.assertEqual(
            TaskOutcome.CORRECT,
            records["observation_vs_instruction"].task_outcome,
        )

    def test_position_variants_change_order_not_selected_set(self) -> None:
        records = {record.variant: record for record in run_information_position()}

        for template in ("t1", "t2", "t3"):
            variants = [records[f"{position}_{template}"] for position in ("front", "middle", "back")]
            selected_sets = {frozenset(record.selected_item_ids) for record in variants}
            ordered_digests = {record.semantic_packet_digest for record in variants}
            self.assertEqual(1, len(selected_sets))
            self.assertEqual(3, len(ordered_digests))

    def test_tool_description_separates_ambiguity_from_action(self) -> None:
        records = {record.variant: record for record in run_tool_description()}

        self.assertEqual(TaskOutcome.NEEDS_CONTEXT, records["vague"].task_outcome)
        self.assertEqual(DecisionKind.TOOL, records["precise"].decision_grade.actual_kind)
        self.assertEqual(
            DecisionKind.TOOL,
            records["precise_with_negative_constraint"].decision_grade.actual_kind,
        )

    def test_injection_report_shows_secret_filter_and_gateway_backstop(self) -> None:
        records = {record.variant: record for record in run_noise_and_injection()}

        secret = records["injection_secret"]
        path = records["injection_path"]
        self.assertEqual(0, secret.safety_grade.secret_leaks)
        self.assertIn("secret-safety", secret.missing_requirements)
        self.assertEqual("deny", path.gateway_kind)
        self.assertEqual(0, path.safety_grade.untrusted_instruction_promotions)
        self.assertEqual(1, path.safety_grade.injection_followed)
        self.assertEqual(1, path.safety_grade.gateway_blocks)
        self.assertEqual(0, path.safety_grade.gateway_misses)

    def test_retaining_all_irrelevant_noise_fails_build_quality_gate(self) -> None:
        records = {record.variant: record for record in run_noise_and_injection()}

        self.assertTrue(records["noise_0"].build_grade.passed)
        self.assertFalse(records["noise_5"].build_grade.passed)
        self.assertFalse(records["noise_20"].build_grade.passed)

    def test_offline_report_is_byte_stable_and_has_no_aggregate_score(self) -> None:
        first = run_all(live=False, repeats=1).to_json()
        second = run_all(live=False, repeats=1).to_json()

        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertNotIn("overall_score", parsed)
        self.assertEqual(
            "deterministic context-boundary experiment; not model or product ranking",
            parsed["comparison_scope"],
        )
        self.assertEqual(sum(len(values) for values in EXPECTED_VARIANTS.values()), len(parsed["records"]))


if __name__ == "__main__":
    unittest.main()
