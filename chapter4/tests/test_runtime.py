from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import PolicyDecision, RunStatus  # noqa: E402
from chapter4.harness.environment import RepairEnvironment  # noqa: E402
from chapter4.harness.policy import (  # noqa: E402
    ScriptedModel,
    canonical_repair_script,
)
from chapter4.harness.runtime import HarnessRuntime, InlineLoop  # noqa: E402
from chapter4.harness.verifier import TestVerifier  # noqa: E402


def _index(outcome, kind: str) -> int:
    return next(
        index for index, event in enumerate(outcome.events)
        if event.kind == kind
    )


class RuntimeTest(unittest.TestCase):
    def test_inline_loop_can_false_complete(self) -> None:
        model = ScriptedModel(
            (PolicyDecision.final("问题已经修复，测试已经通过。"),)
        )
        with RepairEnvironment() as environment:
            outcome = InlineLoop().run(model, environment)
            evidence = TestVerifier().verify(environment)

        self.assertEqual(RunStatus.COMPLETED, outcome.state.status)
        self.assertFalse(evidence.accepted)

    def test_write_pauses_after_checkpoint_and_before_side_effect(self) -> None:
        with RepairEnvironment() as environment:
            runtime = HarnessRuntime(environment.parent / "run-data")
            outcome = runtime.start(
                "run-approval",
                ScriptedModel(canonical_repair_script()),
                environment,
            )

            self.assertEqual(RunStatus.WAITING_APPROVAL, outcome.state.status)
            self.assertEqual(0, environment.side_effect_count("patch-price"))
            self.assertLess(
                _index(outcome, "checkpoint_saved"),
                _index(outcome, "approval_requested"),
            )

    def test_approved_resume_executes_write_once(self) -> None:
        with RepairEnvironment() as environment:
            data_root = environment.parent / "run-data"
            first_process = HarnessRuntime(data_root)
            first_process.start(
                "run-resume",
                ScriptedModel(canonical_repair_script()),
                environment,
            )

            second_process = HarnessRuntime(data_root)
            first = second_process.resume(
                "run-resume",
                approved=True,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )
            second = second_process.resume(
                "run-resume",
                approved=True,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )

            self.assertEqual(RunStatus.COMPLETED, first.state.status)
            self.assertEqual(RunStatus.COMPLETED, second.state.status)
            self.assertEqual(1, environment.side_effect_count("patch-price"))
            self.assertTrue(first.evidence.accepted)
            self.assertEqual(
                environment.state_digest(), first.evidence.state_digest
            )

    def test_receipt_survives_crash_before_terminal_checkpoint(self) -> None:
        """Removing the receipt lookup would replay the patch after recovery."""
        with RepairEnvironment() as environment:
            data_root = environment.parent / "run-data"
            HarnessRuntime(data_root).start(
                "run-receipt-crash",
                ScriptedModel(canonical_repair_script()),
                environment,
            )
            crashing = HarnessRuntime(
                data_root,
                crash_after_receipt_action_ids=frozenset({"patch-price"}),
            )

            with self.assertRaisesRegex(
                RuntimeError, "simulated crash after receipt"
            ):
                crashing.resume(
                    "run-receipt-crash",
                    approved=True,
                    environment=environment,
                    model=ScriptedModel(canonical_repair_script()),
                )

            self.assertEqual(1, environment.side_effect_count("patch-price"))
            recovered = HarnessRuntime(data_root).resume(
                "run-receipt-crash",
                approved=True,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )

            self.assertEqual(RunStatus.COMPLETED, recovered.state.status)
            self.assertEqual(1, environment.side_effect_count("patch-price"))
            self.assertIn(
                "action_deduplicated",
                [event.kind for event in recovered.events],
            )

    def test_approval_is_rejected_when_workspace_digest_changes(self) -> None:
        """Removing the digest comparison would apply an approval to stale code."""
        with RepairEnvironment() as environment:
            data_root = environment.parent / "run-data"
            paused = HarnessRuntime(data_root).start(
                "run-stale-approval",
                ScriptedModel(canonical_repair_script()),
                environment,
            )
            approval = next(
                event for event in paused.events
                if event.kind == "approval_requested"
            )
            self.assertEqual(
                paused.state.state_digest,
                approval.data.get("state_digest"),
            )
            self.assertIsNotNone(paused.state.state_digest)
            pricing = environment.root / "pricing.py"
            pricing.write_text(
                pricing.read_text(encoding="utf-8") + "\n# concurrent edit\n",
                encoding="utf-8",
            )

            outcome = HarnessRuntime(data_root).resume(
                "run-stale-approval",
                approved=True,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )

            self.assertEqual(RunStatus.APPROVAL_STALE, outcome.state.status)
            self.assertEqual("approval_stale", outcome.state.failure_code)
            self.assertEqual(0, environment.side_effect_count("patch-price"))
            self.assertIn(
                "approval_stale", [event.kind for event in outcome.events]
            )

    def test_verifier_runs_from_explicit_verifying_state(self) -> None:
        """Removing the transition would make the state diagram fictional."""
        model = ScriptedModel((PolicyDecision.final("已经完成。"),))
        with RepairEnvironment() as environment:
            outcome = HarnessRuntime(environment.parent / "run-data").start(
                "run-verifying-state", model, environment
            )

        started = next(
            event for event in outcome.events
            if event.kind == "verification_started"
        )
        self.assertEqual("verifying", started.data.get("status"))
        self.assertLess(
            _index(outcome, "verification_started"),
            _index(outcome, "verification"),
        )

    def test_verifier_rejects_premature_final_message(self) -> None:
        model = ScriptedModel((PolicyDecision.final("已经完成。"),))
        with RepairEnvironment() as environment:
            outcome = HarnessRuntime(environment.parent / "run-data").start(
                "run-premature", model, environment
            )

        self.assertEqual(RunStatus.FAILED_VERIFICATION, outcome.state.status)
        self.assertEqual("verification_rejected", outcome.state.failure_code)


if __name__ == "__main__":
    unittest.main()
