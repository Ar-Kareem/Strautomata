
def policy(piles: list[int]) -> str:
    # Ensure we always return a legal move, even on unexpected input.
    if not isinstance(piles, list) or len(piles) != 4:
        return "0,1"

    # Gather pile information
    nonzero = [i for i, x in enumerate(piles) if x > 0]
    if not nonzero:
        # Terminal/unexpected; must still return a string.
        return "0,1"

    ones = sum(1 for x in piles if x == 1)
    big_indices = [i for i, x in enumerate(piles) if x > 1]
    big_count = len(big_indices)

    # Case 1: all nonzero piles are 1
    if big_count == 0:
        # Winning if we can leave an odd number of 1-heaps to opponent.
        # If ones is even, remove one whole heap.
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile > 1
    if big_count == 1:
        i = big_indices[0]
        x = piles[i]
        # Leave odd number of 1-heaps to opponent:
        # if ones is odd -> reduce big pile to 1
        # if ones is even -> reduce big pile to 0
        target = 1 if (ones % 2 == 1) else 0
        take = x - target
        if 1 <= take <= x:
            return f"{i},{take}"

    # Case 3: at least two piles > 1
    # Play normal Nim: move to xor 0 if possible.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(piles):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # Fallback: no winning move or unexpected issue; return any legal move.
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"

    # Should never happen if game state is valid.
    return "0,1"
