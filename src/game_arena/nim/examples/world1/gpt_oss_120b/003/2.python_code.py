
def policy(piles):
    """
    Return a legal move for misère Nim (4 piles) in the form "pile,take".
    piles: list[int] of length 4, current pile sizes.
    The player who takes the last object loses.
    """
    # indices of non‑empty piles
    non_empty = [i for i, v in enumerate(piles) if v > 0]
    if not non_empty:                     # terminal position – no legal move
        return "0,0"

    # ---- Case 1: all piles are 0 or 1 (misère special case) ----
    if all(v <= 1 for v in piles):
        # Count how many piles have a single object
        ones = sum(v for v in piles)      # same as number of non‑empty piles here
        # The winning move is to make the number of remaining 1‑piles even.
        # The simplest: remove a whole pile (take the single object) from any pile.
        # If the count is already even we are losing; any move works.
        for i, v in enumerate(piles):
            if v == 1:
                return f"{i},1"

    # ---- Case 2: at least one pile > 1 (normal Nim rule) ----
    xor = 0
    for v in piles:
        xor ^= v

    if xor == 0:
        # Losing position – just take 1 from the first non‑empty pile
        pile = non_empty[0]
        return f"{pile},1"
    else:
        # Find a pile we can reduce to make xor zero
        for i, v in enumerate(piles):
            target = v ^ xor
            if target < v:
                take = v - target
                return f"{i},{take}"

        # Fallback (should never be reached)
        pile = non_empty[0]
        return f"{pile},1"
