
def policy(piles: list[int]) -> str:
    """
    Misère Nim (last move loses) for exactly 4 piles.
    Returns a legal move "pile,take" with pile in [0..3] and 1 <= take <= piles[pile].
    """
    if len(piles) != 4:
        # Arena guarantees length 4, but keep safe behavior.
        piles = (piles + [0, 0, 0, 0])[:4]

    # Identify piles
    ones = sum(1 for h in piles if h == 1)
    big_indices = [i for i, h in enumerate(piles) if h > 1]
    big_count = len(big_indices)

    # Case 1: All heaps are 0/1 -> parity game on number of 1s.
    if big_count == 0:
        # Must take 1 from some pile that has 1 (if any).
        # Winning iff ones is even; in either case we return a legal move.
        for i, h in enumerate(piles):
            if h == 1:
                return f"{i},1"
        # No legal move exists if all piles are 0; this state should not be queried.
        # (Can't produce a legal move here.)
        return "0,0"  # unreachable in proper gameplay

    # Case 2: Exactly one heap > 1 -> misère special rule.
    if big_count == 1:
        i = big_indices[0]
        h = piles[i]
        # Other heaps are only 0/1; choose to leave an odd number of ones.
        # If we reduce big heap to 0 -> ones stays the same.
        # If we reduce big heap to 1 -> ones increases by 1.
        if ones % 2 == 1:
            # Leave ones unchanged (odd): take entire heap.
            take = h
        else:
            # Make ones odd by leaving a 1: take h-1.
            take = h - 1
        # Safety: ensure legal
        if take < 1:
            take = 1
        if take > piles[i]:
            take = piles[i]
        return f"{i},{take}"

    # Case 3: Two or more heaps > 1 -> play like normal Nim.
    x = 0
    for h in piles:
        x ^= h

    if x == 0:
        # Losing position under perfect play; return any legal move.
        for i, h in enumerate(piles):
            if h > 0:
                return f"{i},1"
        return "0,0"  # unreachable in proper gameplay

    # Find a heap to reduce so that XOR becomes 0.
    for i, h in enumerate(piles):
        target = h ^ x
        if target < h:
            take = h - target
            if 1 <= take <= h:
                return f"{i},{take}"

    # Fallback (should never happen): make any legal move.
    for i, h in enumerate(piles):
        if h > 0:
            return f"{i},1"
    return "0,0"  # unreachable in proper gameplay
