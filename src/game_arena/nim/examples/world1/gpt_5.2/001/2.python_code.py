
def policy(piles: list[int]) -> str:
    """
    Misère Nim (last move loses) optimal policy for exactly 4 piles.
    Returns a legal move string: "pile,take" where pile is 0..3 and take >= 1.
    """
    # Basic safety (arena should always provide length-4 nonnegative ints)
    if not isinstance(piles, list) or len(piles) != 4:
        # Best effort fallback (cannot guarantee legality without a valid state)
        return "0,1"

    nonzero = [i for i, s in enumerate(piles) if s > 0]
    if not nonzero:
        # Terminal state should not be queried; no legal move exists.
        # Return something syntactically valid.
        return "0,1"

    big_indices = [i for i, s in enumerate(piles) if s > 1]
    k = len(big_indices)

    # Case 1: all heaps are size 1 (or 0)
    if k == 0:
        # Remove a whole 1-heap (take 1 from any non-empty pile).
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one heap > 1 (special misère handling)
    if k == 1:
        bi = big_indices[0]
        bsize = piles[bi]
        ones_elsewhere = sum(1 for j, s in enumerate(piles) if j != bi and s == 1)

        # If ones_elsewhere is even, leave big heap as 1; else take it to 0.
        new_size = 1 if (ones_elsewhere % 2 == 0) else 0
        take = bsize - new_size  # bsize > 1 so take >= 1
        return f"{bi},{take}"

    # Case 3: at least two heaps > 1 => play normal Nim (make xor == 0)
    x = 0
    for s in piles:
        x ^= s

    if x == 0:
        # Losing position: guaranteed legal fallback.
        i = nonzero[0]
        return f"{i},1"

    for i, s in enumerate(piles):
        target = s ^ x
        if target < s:
            take = s - target
            # take is guaranteed >= 1 and <= s
            return f"{i},{take}"

    # Should be unreachable; fallback to a legal move.
    i = nonzero[0]
    return f"{i},1"
