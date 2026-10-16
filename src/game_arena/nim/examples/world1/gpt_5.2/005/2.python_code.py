
from typing import List

def policy(piles: List[int]) -> str:
    # Safety: if no legal moves exist (terminal), this should not be called in a proper game loop.
    total = sum(piles)
    if total == 0:
        return "0,0"  # unreachable in standard play; no legal move exists

    # Misère special case: all heaps are size 0 or 1
    if max(piles) <= 1:
        ones = sum(1 for x in piles if x == 1)
        # Winning iff ones is even; remove one from any non-empty pile.
        # If ones is even, leaving ones-1 (odd) is optimal.
        for i, x in enumerate(piles):
            if x == 1:
                return f"{i},1"
        # Fallback (shouldn't happen because total>0 and max<=1 implies at least one 1)
        return "0,0"

    # Normal Nim strategy when at least one heap > 1
    nim_sum = 0
    for x in piles:
        nim_sum ^= x

    if nim_sum == 0:
        # Losing position under perfect play; make any legal move (take 1 from first non-empty pile)
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
        return "0,0"

    # Find a pile to reduce so that overall nim-sum becomes 0
    for i, x in enumerate(piles):
        target = x ^ nim_sum
        if target < x:
            take = x - target
            # Ensure legality
            if 1 <= take <= x:
                return f"{i},{take}"

    # Fallback: should never happen, but ensure a legal move
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"
    return "0,0"
