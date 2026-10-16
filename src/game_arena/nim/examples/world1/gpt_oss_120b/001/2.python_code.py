
def policy(piles):
    """
    Return a legal move string "pile,take" for misère Nim with 4 piles.

    Args:
        piles (list[int]): list of length 4, the current276 pile sizes.

    Returns:
        str: move in the format "pile,take".
    """
    # indices of non‑empty piles
    non_empty = [i for i, v in enumerate(piles) if v > 0]

    # If there are no objects left (should not happen when called), return dummy move
    if not non_empty:
        return "0,0"

    # Check whether every non‑empty pile has size 1
    all_ones = all(piles[i] == 1 for i in non_empty)

    if all_ones:
        # Count of piles with a single object
        cnt = len(non_empty)
        # Winning case: even number of 1‑piles → take one from any pile
        # Losing case (odd) → also take one from any pile (no better move exists)
        pile = non_empty[0]
        take = 1
        return f"{pile},{take}"

    # General case: at least one pile > 1
    xor = 0
    for v in piles:
        xor ^= v

    if xor == 0:
        # Losing position – make any legal move (take 1 from first non‑empty pile)
        pile = non_empty[0]
        take = 1
        return f"{pile},{take}"

    # Winning position – find a pile to make xor zero
    for i in non_empty:
        target = piles[i] ^ xor
        if target < piles[i]:
            take = piles[i] - target
            return f"{i},{take}"

    # Fallback (should never be reached)
    pile = non_empty[0]
    take = 1
    return f"{pile},{take}"
