from __future__ import annotations

from .contracts import VerificationEvidence
from .environment import RepairEnvironment


class TestVerifier:
    def verify(self, environment: RepairEnvironment) -> VerificationEvidence:
        result = environment.run_tests()
        return VerificationEvidence(
            accepted=result.ok,
            summary="tests passed" if result.ok else "tests failed",
            state_digest=environment.state_digest(),
            test_exit_code=0 if result.ok else 1,
        )
