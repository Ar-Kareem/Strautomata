
from __future__ import annotations

from functools import reduce
from operator import ixor
from typing import List


def policy(piles: List[int]) -> str:
    """
    Returns a legal move 'pile,take' for 4-pile misère Nim (taking last loses),
    using optimal play.
    """
    # Defensive: ensure we can always output a legal move when one exists.
    def fallback_move() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal position (no legal moves exist). The arena should not call policy here.
        return "0,0"

    if not isinstance(piles, list) or len(piles) != 4:
        return fallback_move()

    for p in piles:
        if not isinstance(p, int) or p < 0:
            return fallback_move()

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big = len(big_indices)

    # Case 1: all heaps are 0/1 (pure misère endgame)
    if big == 0:
        if ones == 0:
            return fallback_move()  # terminal
        # Winning if ones is even, losing if ones is odd; either way must take one.
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        return fallback_move()

    # Case 2: exactly one heap > 1 (special misère rule)
    if big == 1:
        i = big_indices[0]
        p = piles[i]
        if p <= 1:
            return fallback_move()

        if ones % 2 == 0:
            # Leave opponent an odd number of 1-heaps by making this heap size 1.
            take = p - 1
            if 1 <= take <= p:
                return f"{i},{take}"
        else:
            # Leave opponent an odd number of 1-heaps by removing this heap entirely.
            take = p
            if 1 <= take <= p:
                return f"{i},{take}"

        return fallback_move()

    # Case 3: at least two heaps > 1 => play normal Nim (xor-to-zero)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum == 0:
        # Losing position under optimal play; make any legal move.
        return fallback_move()

    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            if 1 <= take <= p:
                return f"{i},{take}"

    # Should never happen, but ensure legality.
    return fallback_move()
