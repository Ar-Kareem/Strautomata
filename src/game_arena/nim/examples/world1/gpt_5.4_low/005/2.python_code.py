
def policy(piles: list[int]) -> str:
    # Collect basic information
    nonzero_indices = [i for i, x in enumerate(piles) if x > 0]

    # Fallback: if somehow called on a terminal state, return a syntactically valid move.
    # In a proper game engine this should never happen because no legal move exists.
    if not nonzero_indices:
        return "0,1"

    ones = sum(1 for x in piles if x == 1)
    big_indices = [i for i, x in enumerate(piles) if x > 1]
    big = len(big_indices)

    # Case 1: all nonzero piles are size 1
    if big == 0:
        # Only legal move is removing 1 from some nonzero pile.
        # If count is even, this is winning; if odd, position is losing and any move is fine.
        i = nonzero_indices[0]
        return f"{i},1"

    # Case 2: exactly one pile is larger than 1
    if big == 1:
        i = big_indices[0]
        heap = piles[i]
        # Leave opponent an odd number of 1-heaps
        target = 1 if (ones % 2 == 0) else 0
        take = heap - target
        if take >= 1:
            return f"{i},{take}"

    # Case 3: at least two piles larger than 1
    # Play normal Nim: move to nim-sum 0 if possible.
    x = 0
    for h in piles:
        x ^= h

    if x != 0:
        for i, h in enumerate(piles):
            target = h ^ x
            if target < h:
                take = h - target
                if 1 <= take <= h:
                    return f"{i},{take}"

    # Losing position or unexpected edge case: return a guaranteed legal move.
    i = nonzero_indices[0]
    return f"{i},1"
