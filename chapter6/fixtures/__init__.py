"""Deterministic fixtures used by the Chapter 6 continuity experiments."""

from .price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    CANONICAL_TRAJECTORY_DIGEST,
    CANONICAL_WORKSPACE_DIGEST,
    canonical_seed,
    canonical_trajectory,
)

__all__ = [
    "CANONICAL_COMPACTION_CURSOR",
    "CANONICAL_TRAJECTORY_DIGEST",
    "CANONICAL_WORKSPACE_DIGEST",
    "canonical_seed",
    "canonical_trajectory",
]
