from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import ToolCall  # noqa: E402
from chapter4.harness.environment import RepairEnvironment  # noqa: E402
from chapter4.harness.gateway import ActionGateway  # noqa: E402
from chapter4.harness.path_guard import (  # noqa: E402
    PathGuardViolation,
    WorkspacePathGuard,
)


def _patch(path: str) -> ToolCall:
    return ToolCall(
        call_id=f"call-{path}",
        action_id=f"write-{path}",
        name="apply_patch",
        arguments={"path": path, "old": "before", "new": "after"},
    )


class GatewayAndPathGuardTest(unittest.TestCase):
    def test_policy_denies_known_sensitive_path(self) -> None:
        decision = ActionGateway().evaluate(_patch(".env"))

        self.assertEqual("deny", decision.kind.value)
        self.assertEqual("protected_path", decision.reason)

    def test_normal_project_patch_requires_approval(self) -> None:
        decision = ActionGateway().evaluate(_patch("pricing.py"))

        self.assertEqual("ask", decision.kind.value)
        self.assertEqual("side_effect_requires_approval", decision.reason)

    def test_missing_argument_is_denied_before_policy(self) -> None:
        """Returning the old reason would overstate JSON Schema validation."""
        call = ToolCall(
            call_id="call-invalid",
            action_id="invalid-patch",
            name="apply_patch",
            arguments={"path": "pricing.py", "old": "before"},
        )

        decision = ActionGateway().evaluate(call)

        self.assertEqual("deny", decision.kind.value)
        self.assertEqual("missing_required_arguments", decision.reason)

    def test_path_guard_blocks_escape_even_when_soft_policy_allows(self) -> None:
        """Removing path normalization would let this proposal escape root."""
        gateway = ActionGateway(require_approval_for_writes=False)
        call = _patch("../secret.txt")
        self.assertEqual("allow", gateway.evaluate(call).kind.value)

        with RepairEnvironment() as environment:
            guard = WorkspacePathGuard(environment.root)
            with self.assertRaises(PathGuardViolation):
                guard.resolve("../secret.txt", for_write=True)

    def test_path_guard_accepts_legal_project_file(self) -> None:
        with RepairEnvironment() as environment:
            path = WorkspacePathGuard(environment.root).resolve(
                "pricing.py", for_write=True
            )

            self.assertEqual(environment.root / "pricing.py", path)


if __name__ == "__main__":
    unittest.main()
