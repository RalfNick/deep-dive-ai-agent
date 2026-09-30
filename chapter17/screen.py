"""Synthetic screen action gateway. Never invokes OS input APIs."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Frame:
    frame_id: str
    captured_at_ms: int
    image_width: int
    image_height: int
    display_width: int
    display_height: int
    targets: dict[str, tuple[int, int, int, int]]
    state: dict[str, bool]


@dataclass(frozen=True)
class ActionProposal:
    frame_id: str
    action: str
    target_id: str
    image_x: int
    image_y: int
    expected_state: tuple[str, bool]


@dataclass(frozen=True)
class ActionReceipt:
    frame_id: str
    status: Literal["verified", "blocked", "refresh", "unknown"]
    executed: bool
    display_xy: tuple[int, int] | None
    post_frame_id: str | None
    reasons: tuple[str, ...]


def simulate_action(proposal: ActionProposal, current: Frame, after: Frame | None,
                    *, now_ms: int, allowed_actions: frozenset[str], approved: bool) -> ActionReceipt:
    def result(status: Literal["verified", "blocked", "refresh", "unknown"],
               reason: str, *, executed: bool = False,
               xy: tuple[int, int] | None = None, post: str | None = None) -> ActionReceipt:
        return ActionReceipt(proposal.frame_id, status, executed, xy, post, (reason,))

    if current.frame_id != proposal.frame_id:
        return result("refresh", "frame-id-changed")
    if now_ms < current.captured_at_ms or now_ms - current.captured_at_ms > 2000:
        return result("refresh", "frame-stale-or-future")
    if proposal.action not in allowed_actions or not approved:
        return result("blocked", "action-not-authorized")
    if min(current.image_width, current.image_height,
           current.display_width, current.display_height) <= 0:
        return result("blocked", "invalid-screen-dimensions")
    if not (0 <= proposal.image_x < current.image_width and
            0 <= proposal.image_y < current.image_height):
        return result("blocked", "coordinate-outside-frame")
    box = current.targets.get(proposal.target_id)
    if box is None or not (0 <= box[0] <= proposal.image_x <= box[2] < current.image_width and
                           0 <= box[1] <= proposal.image_y <= box[3] < current.image_height):
        return result("blocked", "target-not-at-coordinate")
    xy = (proposal.image_x * current.display_width // current.image_width,
          proposal.image_y * current.display_height // current.image_height)
    # A simulated action has occurred; only a subsequent distinct frame can verify it.
    if after is None:
        return result("unknown", "no-post-frame", executed=True, xy=xy)
    if after.frame_id == current.frame_id or after.captured_at_ms <= now_ms:
        return result("unknown", "post-frame-not-newer", executed=True, xy=xy,
                      post=after.frame_id)
    key, expected = proposal.expected_state
    if after.state.get(key) is not expected:
        return result("unknown", "expected-state-not-observed", executed=True, xy=xy,
                      post=after.frame_id)
    return result("verified", "post-state-observed", executed=True, xy=xy,
                  post=after.frame_id)
