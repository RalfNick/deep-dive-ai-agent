from chapter18.contracts import BudgetLimits


def test_workers_cannot_spend_two_reserved_verification_calls():
    from chapter18.budget import BudgetLedger
    ledger = BudgetLedger(BudgetLimits())
    assert all(ledger.charge(purpose="worker") for _ in range(14))
    assert ledger.charge(purpose="worker") is False
    assert ledger.charge(purpose="verifier") is True
    assert ledger.charge(purpose="verifier") is True
    assert ledger.charge(purpose="verifier") is False
    assert (ledger.used, ledger.remaining) == (16, 0)


def test_reserve_remains_unavailable_after_verifier_consumes_it():
    from chapter18.budget import BudgetLedger
    ledger = BudgetLedger(BudgetLimits(tool_calls=4))
    assert ledger.charge(purpose="verifier")
    assert ledger.charge(purpose="verifier")
    assert ledger.charge(purpose="worker")
    assert ledger.charge(purpose="worker")
    assert not ledger.charge(purpose="worker")
