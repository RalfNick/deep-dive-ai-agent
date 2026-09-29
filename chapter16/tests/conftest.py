import pytest
from chapter16.fixtures import load_fixtures

@pytest.fixture
def lab():
    return load_fixtures()

@pytest.fixture
def baseline():
    from chapter16.artifacts import empty_snapshot
    return empty_snapshot()

@pytest.fixture
def candidate(lab):
    from chapter16.feedback import admit_feedback
    from chapter16.lessons import propose_lessons
    from chapter16.artifacts import build_candidate
    from chapter16.contracts import CLOCK
    blocked = frozenset(t.family_id for t in lab.tasks if t.split == "holdout")
    return build_candidate(propose_lessons(admit_feedback(lab.feedback, lab.sources), lab.replays,
                                         blocked_families=blocked), now=CLOCK)

@pytest.fixture
def use_policy():
    from chapter16.contracts import STEPS, UsePolicy
    return UsePolicy(frozenset(), frozenset(), STEPS + ("open_settings", "export_csv"))
