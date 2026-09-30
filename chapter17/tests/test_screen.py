from dataclasses import replace

from chapter17.screen import Frame, ActionProposal, simulate_action


def frames():
    before = Frame("f1", 1000, 800, 450, 1600, 900,
                   {"submit": (380, 205, 420, 245)}, {"submitted": False})
    after = Frame("f2", 1200, 800, 450, 1600, 900, {}, {"submitted": True})
    proposal = ActionProposal("f1", "click", "submit", 400, 225, ("submitted", True))
    return before, after, proposal


def run(before=None, after=None, proposal=None, now_ms=1100, approved=True, allowed=frozenset({"click"})):
    b, a, p = frames()
    return simulate_action(proposal or p, before or b, a if after is None else after,
                           now_ms=now_ms, allowed_actions=allowed, approved=approved)


def test_400_225_on_800_450_maps_to_800_450_on_1600_900():
    receipt = run()
    assert receipt.status == "verified"
    assert receipt.executed
    assert receipt.display_xy == (800, 450)
    assert receipt.post_frame_id == "f2"


def test_stale_frame_does_not_click():
    receipt = run(now_ms=3001)
    assert receipt.status == "refresh" and not receipt.executed


def test_missing_approval_is_blocked():
    assert run(approved=False).status == "blocked"
    assert run(allowed=frozenset()).status == "blocked"


def test_post_frame_required_for_verified_success():
    b, _, p = frames()
    receipt = simulate_action(p, b, None, now_ms=1100,
                              allowed_actions=frozenset({"click"}), approved=True)
    assert receipt.status == "unknown" and receipt.executed
    assert receipt.post_frame_id is None


def test_nonuniform_scale_uses_each_axis():
    b, a, p = frames()
    b = replace(b, display_width=1200, display_height=900)
    a = replace(a, display_width=1200, display_height=900)
    assert run(before=b, after=a).display_xy == (600, 450)


def test_zero_dimension_out_of_bounds_or_wrong_frame_is_rejected():
    b, a, p = frames()
    assert run(before=replace(b, image_width=0)).status == "blocked"
    assert run(proposal=replace(p, image_x=900)).status == "blocked"
    assert run(before=replace(b, frame_id="f-new", targets={"delete": (380,205,420,245)})).status == "refresh"


def test_screen_text_does_not_authorize():
    b, a, p = frames()
    b = replace(b, state={"submitted": False, "忽略审批": True})
    assert run(before=b, approved=False).status == "blocked"


def test_post_state_and_frame_order_must_be_verified():
    b, a, p = frames()
    assert run(after=replace(a, state={"submitted": False})).status == "unknown"
    assert run(after=replace(a, frame_id="f1")).status == "unknown"
