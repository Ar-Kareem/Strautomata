
"""
Simplified Blackjack-like policy.

We have a private 13-card deck: A,2,3,4,5,6,7,8,9,10,J,Q,K (one copy each).
On each decision we know our current hand and the fixed target.

Policy approach:
- Infer remaining cards (since the deck is unique ranks).
- Compute the best achievable hand value under the target using standard Ace adjustment.
- Choose HIT vs STAY by exact expectation over the remaining deck, assuming future play is optimal.
- Utility = final_value if not bust, else -bust_penalty (penalty depends on target).

This is an optimal stopping DP under a finite deck with no replacement.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Tuple

# Rank indexing for a compact remaining-card bitmask
_RANKS: Tuple[str, ...] = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
_RANK_TO_IDX: Dict[str, int] = {r: i for i, r in enumerate(_RANKS)}
_FULL_MASK: int = (1 << len(_RANKS)) - 1

# Non-ace values by index; Ace handled separately.
_NON_ACE_VALUE = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10,
}


def _best_value_under_target(total_non_ace: int, num_aces: int, target: int) -> Tuple[int, bool]:
    """
    Return (best_value, bust_flag) where best_value is the maximum <= target achievable
    by counting some aces as 11 and the rest as 1. If even all aces as 1 bust, bust_flag=True.
    """
    # Start with all aces as 11
    total = total_non_ace + 11 * num_aces
    aces_as_11 = num_aces
    # Reduce some aces from 11 to 1 (i.e., -10) until under target or no aces left to reduce
    while total > target and aces_as_11 > 0:
        total -= 10
        aces_as_11 -= 1
    return total, (total > target)


# Cache solvers per target to reuse across multiple calls in the same game.
_SOLVER_BY_TARGET: Dict[int, Tuple[float, object]] = {}


def _get_solver(target: int):
    """
    Return (bust_penalty, V) where V(mask, total_non_ace, num_aces) gives optimal expected utility.
    """
    if target in _SOLVER_BY_TARGET:
        return _SOLVER_BY_TARGET[target]

    # Bust penalty: strong negative, slightly increasing with target.
    # Chosen to discourage reckless busting but still allow calculated aggression.
    bust_penalty = 1.1 * float(target) + 10.0

    @lru_cache(maxsize=None)
    def V(mask: int, total_non_ace: int, num_aces: int) -> float:
        value, bust = _best_value_under_target(total_non_ace, num_aces, target)
        if bust:
            return -bust_penalty

        # If no cards remain, must stay.
        if mask == 0:
            return float(value)

        # Option 1: STAY now
        stay_u = float(value)

        # Option 2: HIT now, then continue optimally
        # Next card is effectively uniform over remaining ranks.
        hit_sum = 0.0
        n = 0

        m = mask
        while m:
            lsb = m & -m
            i = (lsb.bit_length() - 1)
            m ^= lsb
            rank = _RANKS[i]

            new_mask = mask & ~lsb
            if rank == "A":
                new_u = V(new_mask, total_non_ace, num_aces + 1)
            else:
                new_u = V(new_mask, total_non_ace + _NON_ACE_VALUE[rank], num_aces)

            hit_sum += new_u
            n += 1

        hit_u = hit_sum / max(n, 1)

        return hit_u if hit_u > stay_u else stay_u

    _SOLVER_BY_TARGET[target] = (bust_penalty, V)
    return bust_penalty, V


def policy(hand: list[str], target: int) -> str:
    """
    Required API: decide "HIT" or "STAY".
    Always returns a legal move string.
    """
    # Defensive handling of target
    try:
        target = int(target)
    except Exception:
        return "STAY"

    # Build remaining-card mask and current totals
    mask = _FULL_MASK
    total_non_ace = 0
    num_aces = 0

    if hand is None:
        hand = []

    for c in hand:
        if not isinstance(c, str):
            continue
        idx = _RANK_TO_IDX.get(c)
        if idx is not None:
            mask &= ~(1 << idx)  # remove from remaining (unique ranks; safe if repeated)
        if c == "A":
            num_aces += 1
        else:
            v = _NON_ACE_VALUE.get(c)
            if v is not None:
                total_non_ace += v

    current_value, bust = _best_value_under_target(total_non_ace, num_aces, target)
    if bust:
        return "STAY"  # already busted; no further action matters, but must return legal string

    # If no cards left, cannot hit
    if mask == 0:
        return "STAY"

    _, V = _get_solver(target)

    # Compare immediate STAY utility vs expected utility of HIT (with optimal continuation)
    stay_u = float(current_value)

    hit_sum = 0.0
    n = 0
    m = mask
    while m:
        lsb = m & -m
        i = (lsb.bit_length() - 1)
        m ^= lsb
        rank = _RANKS[i]

        new_mask = mask & ~lsb
        if rank == "A":
            hit_sum += V(new_mask, total_non_ace, num_aces + 1)
        else:
            hit_sum += V(new_mask, total_non_ace + _NON_ACE_VALUE[rank], num_aces)
        n += 1

    hit_u = hit_sum / max(n, 1)

    # Tie-break toward STAY to reduce variance/bust risk.
    return "HIT" if hit_u > stay_u else "STAY"
