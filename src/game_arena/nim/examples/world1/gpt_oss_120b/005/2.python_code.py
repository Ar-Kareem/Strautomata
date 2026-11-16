
def policy(piles):
    """
    Return a legal move for misère Nim with 4 piles.
    Move format: "pile,take" (both integers, comma‑separated).
    The player who takes the last object loses.
    """
    # Helper: find first non‑empty pile index
    def first_nonzero():
        for i, v in enumerate(piles):
            if v > 0:
                return i
        return -1  # should not happen in a legal call

    # Case 1: all piles are 0 or 1
    if max(piles) <= 1:
        ones = sum(1 for v in piles if v == 1)
        if ones % 2 == 0:
            # Winning: remove an entire pile (take 1)
            for i, v in enumerate(piles):
                if v == 1:
                    return f"{i},1"
        else:
            # Losing: any legal move (remove 1 from first non‑empty pile)
            idx = first_nonzero()
            return f"{idx},1"

    # Case 2: at least one pile > 1  (normal Nim strategy)
    nim_sum = 0
    for v in piles:
        nim_sum ^= v

    if nim_sum == 0:
        # Losing position: make a minimal move
        idx = first_nonzero()
        return f"{idx},1"

    # Find a pile to make nim_sum zero after the move
    for i, v in enumerate(piles):
        target = v ^ nim_sum
        if target < v:
            take = v - target
            return f"{i},{take}"

    # Fallback (should never be reached)
    idx = first_nonzero()
    return f"{idx},1"
