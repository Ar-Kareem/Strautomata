
from functools import reduce
from operator import ixor

def policy(piles: list[int]) -> str:
    """
    Optimal policy for misere Nim with 4 piles.
    Return format: 'pile,take'
    Rule: player who takes the last object loses.
    """
    n = len(piles)

    # Legal fallback helper: take 1 from the first non-empty pile.
    def fallback() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # No legal move exists in a terminal state; should not be called by arena.
        # Return syntactically valid-looking move as a last resort.
        return "0,1"

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return fallback()

    big = [(i, p) for i, p in nonzero if p > 1]
    ones_count = sum(1 for p in piles if p == 1)

    # Endgame: all remaining piles are size 1.
    # In misere Nim, positions with an odd number of 1-piles are winning
    # for the player to move; positions with an even number are losing.
    # The only legal move is to remove one singleton.
    if not big:
        return f"{nonzero[0][0]},1"

    # If exactly one pile is bigger than 1, optimal misere play is:
    # - leave an odd number of 1-piles to the opponent if possible.
    # This makes the opponent eventually take the last object.
    if len(big) == 1:
        i, p = big[0]
        # If current number of ones is even, reduce big pile to 1,
        # leaving odd total singletons.
        # If current number of ones is odd, remove the whole big pile,
        # leaving odd total singletons.
        target = 1 if (ones_count % 2 == 0) else 0
        take = p - target
        if 1 <= take <= p:
            return f"{i},{take}"
        return fallback()

    # General case: at least two piles larger than 1.
    # Use normal Nim xor move when possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Losing position under perfect play, or no xor move found:
    # make a safe move. Prefer reducing a large pile by 1 while keeping options open.
    for i, p in enumerate(piles):
        if p > 1:
            return f"{i},1"

    return fallback()
