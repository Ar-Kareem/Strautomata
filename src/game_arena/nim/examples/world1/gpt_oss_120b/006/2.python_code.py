
def policy(piles):
    """
    Perfect misère Nim policy for 4 piles.

    Parameters
    ----------
    piles : list[int]
        List of 4 non‑negative integers representing the current piles.

    Returns
    -------
    str
        Move in the format "pile,take".
    """
    # Helper: find first non‑empty pile index
    def first_nonzero():
        for i, v in enumerate(piles):
            if v > 0:
                return i
        return -1  # should never happen (game already finished)

    # Count non‑empty piles and check if all are size 1
    nonzero_counts = [v for v in piles if v > 0]
    all_ones = all(v == 1 for v in nonzero_counts)

    # Case 1: all non‑empty piles are size 1 (misère endgame)
    if all_ones:
        # Remove one whole pile (take 1 from any non‑empty pile)
        idx = first_nonzero()
        return f"{idx},1"

    # Case 2: at least one pile > 1 -> play normal Nim logic
    xor_sum = 0
    for v in piles:
        xor_sum ^= v

    if xor_sum != 0:
        # Find a heap that can be reduced to make xor_sum zero
        for i, heap in enumerate(piles):
            if heap == 0:
                continue
            target = heap ^ xor_sum
            if target < heap:
                take = heap - target
                # Ensure we take at least 1 and not more than heap
                if take >= 1 and take <= heap:
                    return f"{i},{take}"
        # Fallback (should never reach here)
        idx = first_nonzero()
        return f"{idx},1"
    else:
        # Losing position: make any legal move (take 1 from first non‑empty heap)
        idx = first_nonzero()
        return f"{idx},1"
