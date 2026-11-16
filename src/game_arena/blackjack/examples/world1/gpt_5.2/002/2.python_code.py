
"""
Blackjack-like policy for a 13-rank single-suit, no-replacement deck.

API:
    def policy(hand: list[str], target: int) -> str

We choose HIT/STAY by maximizing expected match score versus a mixture
of plausible opponent threshold strategies, using exact recursion with memoization.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple

# Fixed rank order (13 distinct cards)
RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_TO_IDX = {r: i for i, r in enumerate(RANKS)}

# Card "base" values counting Ace as 11 (we later reduce by 10 as needed)
BASE_VALUES = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
IS_ACE = [True] + [False] * 12

FULL_MASK = (1 << 13) - 1

# Precompute for every mask: base sum (Ace=11) and ace count
MASK_BASE_SUM = [0] * (1 << 13)
MASK_ACE_COUNT = [0] * (1 << 13)
for m in range(1 << 13):
    # Build from lowest set bit
    if m == 0:
        continue
    lsb = m & -m
    i = (lsb.bit_length() - 1)
    prev = m ^ lsb
    MASK_BASE_SUM[m] = MASK_BASE_SUM[prev] + BASE_VALUES[i]
    MASK_ACE_COUNT[m] = MASK_ACE_COUNT[prev] + (1 if IS_ACE[i] else 0)


def _hand_value_from_mask(mask: int, target: int) -> int:
    """Best (highest) total <= target if possible by converting Aces 11->1 as needed."""
    total = MASK_BASE_SUM[mask]
    aces = MASK_ACE_COUNT[mask]
    while aces > 0 and total > target:
        total -= 10
        aces -= 1
    return total


def _mask_from_hand(hand: List[str]) -> int:
    mask = 0
    for c in hand:
        i = RANK_TO_IDX.get(c)
        if i is None:
            continue
        mask |= (1 << i)
    return mask


def _opponent_mixture_weights(target: int) -> List[Tuple[int, float]]:
    """
    Returns a mixture over opponent 'margins', where margin means:
        opponent stays when total >= (target - margin).
    Larger margin => more conservative (stops earlier).
    """
    # A robust mix around common "stand a few below target" behaviors
    # (weights sum to 1.0).
    return [
        (6, 0.15),
        (5, 0.10),
        (4, 0.25),
        (3, 0.15),
        (2, 0.20),
        (1, 0.10),
        (0, 0.05),
    ]


@lru_cache(maxsize=None)
def _opp_dist_for_margin(target: int, margin: int, mask: int) -> Tuple[float, ...]:
    """
    Opponent final outcome distribution from current hand mask, under a threshold policy.

    Returns a tuple of length (target+2):
        indices 0..target: probability of finishing exactly at that total (not bust)
        index target+1: bust probability
    """
    bust_idx = target + 1
    total = _hand_value_from_mask(mask, target)

    # Bust
    if total > target:
        arr = [0.0] * (target + 2)
        arr[bust_idx] = 1.0
        return tuple(arr)

    # Stay condition
    stop_threshold = max(0, target - margin)
    if total >= target or total >= stop_threshold or mask == FULL_MASK:
        arr = [0.0] * (target + 2)
        arr[total] = 1.0
        return tuple(arr)

    # Otherwise HIT: average over remaining cards
    remaining = (~mask) & FULL_MASK
    n = remaining.bit_count()
    if n == 0:
        arr = [0.0] * (target + 2)
        arr[total] = 1.0
        return tuple(arr)

    out = [0.0] * (target + 2)
    p = 1.0 / n
    r = remaining
    while r:
        lsb = r & -r
        r ^= lsb
        nxt = mask | lsb
        dist = _opp_dist_for_margin(target, margin, nxt)
        for i, v in enumerate(dist):
            out[i] += p * v
    return tuple(out)


@lru_cache(maxsize=None)
def _opp_mixture_dist(target: int) -> Tuple[float, ...]:
    """Mixture opponent distribution from empty hand."""
    weights = _opponent_mixture_weights(target)
    out = [0.0] * (target + 2)
    total_w = 0.0
    for margin, w in weights:
        total_w += w
        dist = _opp_dist_for_margin(target, margin, 0)
        for i, v in enumerate(dist):
            out[i] += w * v
    if total_w <= 0:
        # Shouldn't happen, but keep it safe
        out[target + 1] = 1.0
        return tuple(out)
    for i in range(len(out)):
        out[i] /= total_w
    return tuple(out)


@lru_cache(maxsize=None)
def _stay_score(target: int, our_total: int) -> float:
    """
    Expected match score if we STAY at our_total.
    Score: WIN=1, DRAW=0.5, LOSS=0
    """
    opp = _opp_mixture_dist(target)
    bust_idx = target + 1

    # If we're busted (shouldn't be used for STAY typically), only draw if opp also busts
    if our_total > target:
        return 0.5 * opp[bust_idx]

    score = opp[bust_idx]  # opponent bust => we win
    our_d = target - our_total

    # Compare distances when opponent doesn't bust
    for o in range(0, target + 1):
        p = opp[o]
        if p <= 0.0:
            continue
        opp_d = target - o
        if our_d < opp_d:
            score += p
        elif our_d == opp_d:
            score += 0.5 * p
        # else: loss contributes 0
    return score


@lru_cache(maxsize=None)
def _value(target: int, mask: int) -> float:
    """
    Optimal expected match score from this hand mask (our turn to decide),
    assuming unknown next card is uniform among remaining.
    """
    opp = _opp_mixture_dist(target)
    bust_idx = target + 1

    total = _hand_value_from_mask(mask, target)

    # If busted, the only non-loss is a draw when opponent also busts
    if total > target:
        return 0.5 * opp[bust_idx]

    # If no cards left or already exactly target, must stay
    if mask == FULL_MASK or total == target:
        return _stay_score(target, total)

    ev_stay = _stay_score(target, total)

    # HIT expectation
    remaining = (~mask) & FULL_MASK
    n = remaining.bit_count()
    if n == 0:
        return ev_stay

    ev_hit = 0.0
    p = 1.0 / n
    r = remaining
    while r:
        lsb = r & -r
        r ^= lsb
        ev_hit += p * _value(target, mask | lsb)

    return ev_hit if ev_hit > ev_stay else ev_stay


def policy(hand: list[str], target: int) -> str:
    """
    Decide the next move: "HIT" or "STAY".
    Always returns a legal action string.
    """
    try:
        if not isinstance(target, int):
            return "STAY"
        # Guard target range, but remain legal regardless.
        if target <= 0:
            return "STAY"

        mask = _mask_from_hand(hand)
        total = _hand_value_from_mask(mask, target)

        # If already bust or at/above target, never hit.
        if total >= target:
            return "STAY"

        # If no remaining cards, must stay.
        if mask == FULL_MASK:
            return "STAY"

        # Compare immediate actions using our value recursion
        ev_stay = _stay_score(target, total)

        remaining = (~mask) & FULL_MASK
        n = remaining.bit_count()
        if n == 0:
            return "STAY"

        ev_hit = 0.0
        p = 1.0 / n
        r = remaining
        while r:
            lsb = r & -r
            r ^= lsb
            ev_hit += p * _value(target, mask | lsb)

        # Tie-break slightly towards STAY (reduces bust risk / avoids needless variance)
        return "HIT" if ev_hit > ev_stay + 1e-12 else "STAY"
    except Exception:
        # Always return a legal move
        return "STAY"
