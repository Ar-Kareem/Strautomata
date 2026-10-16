
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple, Dict

# Single-suit ranks (one copy of each in our personal deck)
RANKS: Tuple[str, ...] = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
RANK_TO_INDEX: Dict[str, int] = {r: i for i, r in enumerate(RANKS)}
ALL_MASK: int = (1 << len(RANKS)) - 1

# Base values with A treated as 11; face cards as 10
BASE_VALUE: Tuple[int, ...] = (11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10)
IS_ACE: Tuple[int, ...] = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# Precompute (base_sum, ace_count) for every subset mask (independent of target)
_MASK_BASE_SUM: List[int] = [0] * (1 << len(RANKS))
_MASK_ACE_COUNT: List[int] = [0] * (1 << len(RANKS))
for mask in range(1, 1 << len(RANKS)):
    lsb = mask & -mask
    i = (lsb.bit_length() - 1)
    prev = mask ^ lsb
    _MASK_BASE_SUM[mask] = _MASK_BASE_SUM[prev] + BASE_VALUE[i]
    _MASK_ACE_COUNT[mask] = _MASK_ACE_COUNT[prev] + IS_ACE[i]


def _adjust_total(base_sum: int, ace_count: int, target: int) -> Tuple[int, bool]:
    """
    Apply the game's Ace rule:
    - Start with A=11, and while total>target convert an Ace from 11 to 1 (i.e., -10).
    Returns (best_total, busted).
    """
    total = base_sum
    aces_left = ace_count
    while total > target and aces_left > 0:
        total -= 10
        aces_left -= 1
    return total, (total > target)


def _utility(total: int, busted: bool, target: int) -> float:
    """
    Bounded utility to optimize closeness to target while avoiding bust:
    - Bust => 0
    - Otherwise, prefer being very close: (1/(1+distance))^2
    """
    if busted:
        return 0.0
    dist = target - total
    # dist should be >= 0 if not busted, but guard anyway
    if dist < 0:
        return 0.0
    u = 1.0 / (1.0 + float(dist))
    return u * u


# Cache DP results per target; each target gets its own value memo.
_VALUE_CACHE: Dict[int, Dict[int, float]] = {}


def _value(mask: int, target: int) -> float:
    """
    Optimal expected utility from state 'mask' (cards currently in hand),
    assuming future draws are uniformly random among remaining ranks.
    """
    # Per-target memo
    tcache = _VALUE_CACHE.setdefault(target, {})
    if mask in tcache:
        return tcache[mask]

    base_sum = _MASK_BASE_SUM[mask]
    ace_count = _MASK_ACE_COUNT[mask]
    total, busted = _adjust_total(base_sum, ace_count, target)

    # If busted, game ends.
    stay_u = _utility(total, busted, target)
    if busted:
        tcache[mask] = stay_u
        return stay_u

    # If no cards remain, must stop.
    if mask == ALL_MASK:
        tcache[mask] = stay_u
        return stay_u

    # Expected value of hitting: average over remaining cards.
    remaining = ALL_MASK ^ mask
    hit_sum = 0.0
    n = 0
    m = remaining
    while m:
        lsb = m & -m
        m ^= lsb
        i = lsb.bit_length() - 1
        n += 1
        hit_sum += _value(mask | (1 << i), target)
    hit_u = hit_sum / float(n) if n else 0.0

    best = hit_u if hit_u > stay_u else stay_u
    tcache[mask] = best
    return best


def policy(hand: List[str], target: int) -> str:
    """
    Return "HIT" or "STAY" (always legal).

    hand: list of ranks currently held.
    target: integer target score (10..30).
    """
    # Defensive: ensure target is an int in a sane range
    try:
        target = int(target)
    except Exception:
        target = 21

    # Build mask from observed hand (ignore unknown/duplicate ranks robustly)
    mask = 0
    for r in hand:
        i = RANK_TO_INDEX.get(r)
        if i is None:
            continue
        mask |= (1 << i)

    base_sum = _MASK_BASE_SUM[mask]
    ace_count = _MASK_ACE_COUNT[mask]
    total, busted = _adjust_total(base_sum, ace_count, target)

    # If already busted, the round is effectively over; return a legal move.
    if busted:
        return "STAY"

    # If no cards remain, cannot improve.
    if mask == ALL_MASK:
        return "STAY"

    # Compare optimal expected utility of staying vs hitting once (then playing optimally).
    stay_u = _utility(total, False, target)

    remaining = ALL_MASK ^ mask
    hit_sum = 0.0
    n = 0
    m = remaining
    while m:
        lsb = m & -m
        m ^= lsb
        i = lsb.bit_length() - 1
        n += 1
        hit_sum += _value(mask | (1 << i), target)
    hit_u = hit_sum / float(n) if n else 0.0

    # Small epsilon to avoid jitter on exact ties
    return "HIT" if hit_u > stay_u + 1e-12 else "STAY"
