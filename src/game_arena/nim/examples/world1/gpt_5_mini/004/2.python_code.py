
from functools import reduce
from operator import xor

def policy(piles: list[int]) -> str:
    """
    Misère Nim policy for 4 piles returning "pile,take".
    - Implements the standard misère-Nim strategy:
      * If no pile has size >1 (all non-zero piles are 1): use parity rule (take 1).
      * Otherwise try to play the normal Nim move (make xor 0).
    - Safeguard: never take all remaining tokens in one move (which would take the last token and lose).
      If the xor-prescribed move would take the last token, instead take 1 from a heap >1 (or from first non-empty).
    """
    # Ensure length 4 (but we don't strictly need to enforce)
    n = len(piles)
    total = sum(piles)
    # If no legal moves (all zero) — return a legal-looking fallback (shouldn't be called in normal play)
    if total == 0:
        # There's no legal move; to satisfy the API return something (though caller should not provide this).
        return "0,1"

    ones = sum(1 for p in piles if p == 1)
    big = sum(1 for p in piles if p > 1)

    # Helper to emit a move
    def fmt(i, t):
        return f"{i},{t}"

    # Case: all non-zero piles are 1 (i.e., no pile >1)
    if big == 0:
        # In this scenario (only 1-sized heaps), best we can do is remove 1 from any non-empty heap.
        for i, p in enumerate(piles):
            if p >= 1:
                return fmt(i, 1)

    # Otherwise, there is at least one heap > 1: attempt normal-Nim xor move
    s = reduce(xor, piles, 0)
    if s != 0:
        # Find a heap to reduce so that new_xor == 0
        for i, p in enumerate(piles):
            target = p ^ s
            if target < p:
                take = p - target
                # Safeguard: if this move would remove all remaining tokens (i.e. take == total),
                # that would take the last object and make us lose — avoid it.
                if take == total:
                    # Prefer to remove 1 from a heap >1 (not finishing the game)
                    for j, q in enumerate(piles):
                        if q > 1:
                            return fmt(j, 1)
                    # Otherwise, remove 1 from the first non-empty pile
                    for j, q in enumerate(piles):
                        if q >= 1:
                            return fmt(j, 1)
                else:
                    return fmt(i, take)

    # If xor == 0 (losing under best play) or we fell through, make a safe fallback move:
    # Prefer removing 1 from a heap >1 (keeps flexibility), else remove 1 from first non-empty heap.
    for i, p in enumerate(piles):
        if p > 1:
            return fmt(i, 1)
    for i, p in enumerate(piles):
        if p >= 1:
            return fmt(i, 1)

    # Fallback (shouldn't reach): pick pile 0 and take 1
    return "0,1"
