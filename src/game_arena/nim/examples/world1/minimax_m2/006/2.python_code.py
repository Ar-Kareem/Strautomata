
def policy(piles: list[int]) -> str:
    """
    Returns a single optimal move for the current position in misère Nim.
    
    Parameters
    ----------
    piles : list[int]
        List of four integers representing the number of objects in each pile.
        The list is never all zeros when this function is called.
    
    Returns
    -------
    str
        A move in the form "pile,take" where `pile` is the 0‑based index
        and `take` is the number of objects to remove (1 <= take <= piles[pile]).
    """
    # Helper: find any non‑empty pile
    def first_nonzero():
        for i, cnt in enumerate(piles):
            if cnt > 0:
                return i
        return None

    # Case 1: all piles are of size 0 or 1  -> misère special case
    if all(p <= 1 for p in piles):
        ones = sum(1 for p in piles if p == 1)
        # If there is an even number of 1‑piles we can win by removing one.
        # If odd, any move loses; we still must return a legal move.
        if ones % 2 == 0:
            # Remove a whole 1‑pile (take = 1)
            idx = next(i for i, p in enumerate(piles) if p == 1)
            return f"{idx},1"
        else:
            # Losing position – just remove any 1‑pile
            idx = next(i for i, p in enumerate(piles) if p == 1)
            return f"{idx},1"

    # Case 2: at least one pile > 1 -> treat as normal Nim
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        # There is a winning move: reduce a pile so that the xor becomes zero
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                return f"{i},{take}"
    else:
        # Losing position – any legal move (here we simply take 1 from the first non‑empty pile)
        idx = first_nonzero()
        # take at least one, but not more than the pile contains
        take = 1 if piles[idx] > 1 else piles[idx]
        return f"{idx},{take}"

    # The code should never reach here because a move always exists
    # (the game is guaranteed to be in a legal state)
    raise RuntimeError("No legal move found")
