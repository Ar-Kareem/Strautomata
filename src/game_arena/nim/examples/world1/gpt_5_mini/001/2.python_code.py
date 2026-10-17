
from typing import List
import operator
from functools import reduce

def policy(piles: List[int]) -> str:
    """
    Misère Nim policy for 4 piles (player who takes the last object loses).
    Returns a move string "pile,take" (pile is 0-based index).
    """
    # Ensure we have a list of ints
    piles = list(map(int, piles))
    n = len(piles)
    # If all piles are zero (game finished) — no legal move exists in reality.
    # Return a safe fallback move (should not be called in proper play).
    if sum(piles) == 0:
        return "0,1"
    # Count heaps of size 1 and check max
    ones = sum(1 for p in piles if p == 1)
    maxp = max(piles)
    # Case: every non-empty pile has size 1 (i.e., max <= 1)
    if maxp <= 1:
        # If even number of ones, current player has a winning move: take one from any 1-heap.
        # If odd, position is losing with best play, but we must still return a legal move.
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # If we reach here, there were no ones (shouldn't happen because sum(piles)>0),
        # fall back to first non-zero (defensive).
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    # General case: there exists a heap >= 2. Play like normal Nim.
    xor = reduce(operator.xor, piles, 0)
    if xor == 0:
        # No winning move under perfect play; return a simple legal move:
        # remove 1 from first non-empty heap.
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    else:
        # Find a heap where reducing it to (pile ^ xor) decreases its size.
        for i, p in enumerate(piles):
            target = p ^ xor
            if target < p:
                take = p - target
                # Ensure take is at least 1 and at most p
                if take < 1:
                    take = 1
                if take > p:
                    take = p
                return f"{i},{take}"
    # Defensive fallback (should not be reached): remove 1 from first non-empty heap.
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    # Final fallback (should never happen)
    return "0,1"
