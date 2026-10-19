
from typing import List

def policy(piles: list[int]) -> str:
    # Misère Nim for 4 piles where taking the last object loses.
    # Handle zero piles safely (still only one move is returned).
    nonzero = [x for x in piles if x > 0]
    if not nonzero:
        # Should never happen because game would have ended,
        # but return a legal fallback.
        return "0,1"

    # If all non-zero piles are size 1, then optimal play is:
    # - If the number of piles with 1 is even, take 1 from any pile (leave odd -> opponent forced to take last and lose).
    # - If odd, take 1 from any pile is losing; but we must play—yet in optimal play this situation won't occur
    #   as winning unless all are size 1; we still choose a legal move that minimizes loss.
    all_ones = all(x == 1 for x in nonzero)
    if all_ones:
        ones_count = sum(1 for x in piles if x == 1)
        # Any move must take 1 from some pile.
        # Under misère Nim with all piles size 1, winning strategy:
        # if ones_count is even -> make move (any) to make remaining odd.
        # if ones_count is odd -> any move makes remaining even (losing), but it's the only legal move.
        for i, x in enumerate(piles):
            if x == 1:
                return f"{i},1"

    # General misère Nim:
    # If there is at least one pile > 1:
    # Use normal Nim strategy: make nim-sum 0 by reducing a pile appropriately.
    # This is optimal for misère Nim except when all non-zero piles are size 1 (handled above).
    nim_sum = 0
    for x in piles:
        nim_sum ^= x

    # If nim_sum == 0 in normal play, current player would be losing; but in misère Nim with
    # the handled exception, this still corresponds to optimal play for the game.
    # We'll still return a legal move that follows the best available reduction logic.
    if nim_sum == 0:
        # Choose a move that flips nim-sum away from 0 with minimal change, avoiding illegal moves.
        # Taking 1 from the first non-empty pile > 0 is always legal.
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"

    # Find a pile where reducing it to (pile_size ^ nim_sum) is possible.
    for i, x in enumerate(piles):
        target = x ^ nim_sum
        if target < x:
            take = x - target
            if 1 <= take <= x:
                return f"{i},{take}"

    # Fallback (should not happen): take 1 from first non-empty pile.
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"
    return "0,1"
