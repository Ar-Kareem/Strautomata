
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Tuple

# Ranks in the single-suit, 13-distinct-card deck.
RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
IDX: Dict[str, int] = {r: i for i, r in enumerate(RANKS)}

# Base values with Ace as 11; Ace softening (11->1) handled separately relative to target.
BASE_VALUE: Dict[str, int] = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}

FULL_MASK: int = (1 << 13) - 1

# Precompute for every possible "drawn mask" (subset of cards already in hand):
# - sum if all Aces are 11
# - number of aces
SUM11_DRAWN: List[int] = [0] * (1 << 13)
ACES_DRAWN: List[int] = [0] * (1 << 13)

# Also precompute remaining-card bit lists for every remaining mask.
REMAINING_BITS: List[List[int]] = [[] for _ in range(1 << 13)]


def _init_tables() -> None:
    for m in range(1 << 13):
        # Build remaining bits list for this remaining mask.
        bits: List[int] = []
        for i in range(13):
            b = 1 << i
            if m & b:
                bits.append(b)
        REMAINING_BITS[m] = bits

    # DP over masks to compute sum/aces for drawn masks.
    for m in range(1 << 13):
        # Use least significant set bit recurrence.
        if m == 0:
            SUM11_DRAWN[m] = 0
            ACES_DRAWN[m] = 0
            continue
        lsb = m & -m
        i = (lsb.bit_length() - 1)
        prev = m ^ lsb
        rank = RANKS[i]
        SUM11_DRAWN[m] = SUM11_DRAWN[prev] + BASE_VALUE[rank]
        ACES_DRAWN[m] = ACES_DRAWN[prev] + (1 if rank == "A" else 0)


_init_tables()

# Memo per target to avoid recomputing across multiple calls within the same game.
_MEMO_BY_TARGET: Dict[int, Dict[int, Tuple[float, str]]] = {}


def _hand_total_from_remaining_mask(remaining_mask: int, target: int) -> int:
    """
    Compute the hand total given remaining cards in deck (so drawn = FULL ^ remaining),
    applying Ace softening (11->1) until total <= target if possible.
    """
    drawn_mask = FULL_MASK ^ remaining_mask
    total = SUM11_DRAWN[drawn_mask]
    aces = ACES_DRAWN[drawn_mask]
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total


def _bust_penalty(target: int) -> float:
    """
    Penalty for busting. Chosen to be worse than any non-bust squared-distance outcome.
    Max non-bust squared distance is target^2 (when total=0), so we go below that.
    """
    # Slightly worse than worst non-bust: -(target^2 + margin)
    # Margin grows mildly with target to keep bust clearly undesirable.
    return -float((target + 5) * (target + 5))


def _solve_best_action(remaining_mask: int, target: int) -> Tuple[float, str]:
    """
    Returns (best_expected_utility, best_action) from this remaining deck state.
    Action is one of "HIT" or "STAY".
    """
    memo = _MEMO_BY_TARGET.setdefault(target, {})
    if remaining_mask in memo:
        return memo[remaining_mask]

    total = _hand_total_from_remaining_mask(remaining_mask, target)
    bust_pen = _bust_penalty(target)

    # If already busted (shouldn't normally be queried), no decisions matter.
    if total > target:
        memo[remaining_mask] = (bust_pen, "STAY")
        return memo[remaining_mask]

    # Utility if we stop now: squared distance to target (closer is much better).
    dist = target - total
    stay_val = -float(dist * dist)
    best_val = stay_val
    best_act = "STAY"

    # Utility if we hit: expectation over all remaining cards, then continue optimally.
    bits = REMAINING_BITS[remaining_mask]
    if bits:
        hit_sum = 0.0
        p = 1.0 / len(bits)
        for b in bits:
            new_mask = remaining_mask & ~b
            v, _ = _solve_best_action(new_mask, target)
            hit_sum += v
        hit_val = hit_sum * p

        if hit_val > best_val:
            best_val = hit_val
            best_act = "HIT"

    memo[remaining_mask] = (best_val, best_act)
    return memo[remaining_mask]


def policy(hand: list[str], target: int) -> str:
    """
    Decide the next move in the simplified Blackjack-like game.

    Args:
        hand: list of card rank strings currently held.
        target: integer target score T.

    Returns:
        "HIT" or "STAY" (always legal).
    """
    # Defensive: ensure target is in expected range.
    if not isinstance(target, int) or target < 1:
        return "STAY"

    # Compute remaining mask from observed hand.
    remaining_mask = FULL_MASK
    for c in hand:
        i = IDX.get(c)
        if i is None:
            # Unknown card label; safest legal action.
            return "STAY"
        remaining_mask &= ~(1 << i)

    # If already at/over target (after Ace adjustment), staying is always safe.
    total = _hand_total_from_remaining_mask(remaining_mask, target)
    if total >= target:
        return "STAY"

    # Use DP-derived optimal action.
    _, act = _solve_best_action(remaining_mask, target)
    return act if act in ("HIT", "STAY") else "STAY"
