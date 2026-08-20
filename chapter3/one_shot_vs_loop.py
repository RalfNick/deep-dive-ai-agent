"""Compare a plausible one-shot answer with a closed-loop execution."""

from __future__ import annotations

from agent_loop import AgentLoop, FIXED_SOURCE, PriceRepo, RepairPolicy


def main() -> None:
    with PriceRepo() as repo:
        before = repo.state_digest()
        one_shot_answer = FIXED_SOURCE
        print("[one-shot] model returned a plausible implementation")
        print(f"[one-shot] answer_chars={len(one_shot_answer)}")
        print(f"[one-shot] file_changed={before != repo.state_digest()}")
        print(f"[one-shot] acceptance_tests_pass={repo.tests_pass()}")
        assert not repo.tests_pass()

    with PriceRepo() as repo:
        before = repo.state_digest()
        result = AgentLoop(
            repo, completion_verifier=repo.verify_completion
        ).run(RepairPolicy())
        after = repo.state_digest()
        print("\n[closed-loop]")
        print(f"status={result.status}")
        print(f"tool_calls={result.tool_calls}")
        print(f"file_changed={before != after}")
        print(f"acceptance_tests_pass={repo.tests_pass()}")
        assert result.status == "completed"


if __name__ == "__main__":
    main()
