
from functools import reduce
import operator
from typing import List

def policy(piles: List[int]) -> str:
    """
    Misère Nim policy for 4 piles (last move loses).
    Returns a move as 'pile,take' where pile is 0-based index and take >= 1.
    """
    # Defensive: ensure length 4 (but work with any length)
    n = len(piles)
    # Find non-empty indices
    nonzeros = [i for i, p in enumerate(piles) if p > 0]
    if not nonzeros:
        # No legal move; but caller should not provide this state.
        # Return a default legal-looking move if possible (will be invalid if truly all zero).
        return "0,1"
    # Count heaps of size 1 and heaps >1
    ones = sum(1 for p in piles if p == 1)
    bigs = sum(1 for p in piles if p > 1)
    # Case: all non-zero piles are size 1 (i.e., bigs == 0)
    if bigs == 0:
        # If number of ones is even -> winning: take 1 from any heap (makes it odd for opponent)
        # If number of ones is odd -> losing: no winning move, still take 1 from any heap
        # In either case, we remove exactly 1 from a heap of size 1
        i = nonzeros[0]
        return f"{i},1"
    # Otherwise, play like normal Nim: compute nim-sum
    nim_sum = reduce(operator.xor, piles, 0)
    if nim_sum == 0:
        # Losing position under optimal play: make a simple legal move (remove 1 from first non-empty)
        i = nonzeros[0]
        return f"{i},1"
    # Find a heap to reduce so that p_i ^ nim_sum < p_i
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            if take >= 1 and take <= p:
                return f"{i},{take}"
    # Fallback (should not reach): remove 1 from first non-empty
    i = nonzeros[0]
    return f"{i},1"
