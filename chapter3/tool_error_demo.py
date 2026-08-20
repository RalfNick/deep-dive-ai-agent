"""Demonstrate typed tool errors, bounded retry, and idempotency keys."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    ok: bool
    value: str
    error_type: str | None = None
    retryable: bool = False


class PaymentTool:
    def __init__(self) -> None:
        self.attempts = 0
        self.side_effects = 0
        self.ledger: dict[str, str] = {}

    def charge(self, *, order_id: str, cents: int, idempotency_key: str) -> Result:
        if cents <= 0:
            return Result(False, "cents must be positive", "invalid_arguments", False)
        self.attempts += 1
        if idempotency_key in self.ledger:
            return Result(True, self.ledger[idempotency_key])
        receipt = f"receipt:{order_id}:{cents}"
        self.ledger[idempotency_key] = receipt
        self.side_effects += 1
        if self.attempts == 1:
            return Result(
                False,
                "response lost after commit",
                "transient_timeout",
                True,
            )
        return Result(True, receipt)


def call_with_retry(tool: PaymentTool, *, cents: int) -> Result:
    key = "order-42-attempt-group"
    for attempt in range(1, 4):
        result = tool.charge(
            order_id="order-42", cents=cents, idempotency_key=key
        )
        print(
            f"attempt={attempt} ok={result.ok} type={result.error_type} "
            f"retryable={result.retryable} value={result.value}"
        )
        if result.ok or not result.retryable:
            return result
    return result


def main() -> None:
    print("[transient failure: retry with the same idempotency key]")
    tool = PaymentTool()
    success = call_with_retry(tool, cents=1990)
    duplicate = tool.charge(
        order_id="order-42", cents=1990, idempotency_key="order-42-attempt-group"
    )
    print(
        f"duplicate_ok={duplicate.ok} attempts={tool.attempts} "
        f"side_effects={tool.side_effects} ledger_entries={len(tool.ledger)}"
    )
    assert success.ok and tool.side_effects == 1 and len(tool.ledger) == 1

    print("\n[permanent failure: do not retry]")
    invalid_tool = PaymentTool()
    failure = call_with_retry(invalid_tool, cents=-1)
    assert not failure.ok and invalid_tool.attempts == 0


if __name__ == "__main__":
    main()
