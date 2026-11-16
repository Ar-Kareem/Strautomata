
from typing import List

def policy(piles: List[int]) -> str:
    """
    Return a legal move for misère Nim (last move loses) on 4 piles.
    Move format: 'pile,take' where pile is 0-based index and 1 <= take <= piles[pile].
    """
    # Helper: find first nonzero pile index
    def first_nonzero_index(ps):
        for i, v in enumerate(ps):
            if v > 0:
                return i
        return None

    # Helper: check whether all nonzero piles are of size 1
    def all_nonzero_are_one(ps):
        found_nonzero = False
        for v in ps:
            if v != 0:
                found_nonzero = True
                if v != 1:
                    return False
        return found_nonzero  # True only if there is at least one nonzero and all such are 1

    # Safety: if there are no stones (shouldn't normally be called), return a dummy legal-ish move
    idx0 = first_nonzero_index(piles)
    if idx0 is None:
        # No legal move exists; return something syntactically legal (but may be invalid in environment).
        # To avoid returning an illegal take > pile, return '0,1' only if piles[0] >= 1, else try others.
        # As a final fallback, return '0,1'.
        return "0,1"

    # Count nonzero and ones
    nonzero_count = sum(1 for v in piles if v > 0)
    ones_count = sum(1 for v in piles if v == 1)

    # Case 1: every nonzero pile is size 1 -> misère parity rule
    if all_nonzero_are_one(piles):
        # Best move: take 1 from any nonzero pile (this is the only legal move per pile)
        # Choose the first nonzero pile.
        i = idx0
        return f"{i},1"

    # Case 2: there is at least one pile > 1 -> use modified Nim rule
    # Compute nim-sum
    nim = 0
    for v in piles:
        nim ^= v

    if nim == 0:
        # Losing position under perfect play; return a safe legal fallback:
        # remove 1 from the largest pile (or first nonzero) to be deterministic.
        # Prefer a pile >1 to avoid accidentally finishing the game.
        best = None
        for i, v in enumerate(piles):
            if v > 1:
                best = i
                break
        if best is None:
            best = idx0
        return f"{best},1"

    # nim != 0 -> try to find a heap to reduce to make nim-sum 0
    for i, v in enumerate(piles):
        target = v ^ nim
        if target < v:
            # compute resulting piles if we make the normal nim reduction
            new_piles = piles.copy()
            new_piles[i] = target
            # If that move would leave every nonzero pile equal to 1, it's the misère trap.
            if all_nonzero_are_one(new_piles):
                # Instead, remove the entire heap i (take v)
                take = v
            else:
                take = v - target
            # Ensure take at least 1 and not greater than v
            if take < 1:
                take = 1
            if take > v:
                take = v
            return f"{i},{take}"

    # Fallback (should not happen): remove 1 from first nonzero pile
    return f"{idx0},1"
