
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Defensive normalization in case the arena passes unusual int-like values.
    piles = [int(x) for x in piles]

    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # Terminal state should normally never be queried.
    # No legal move exists here, but return a harmless formatted fallback.
    if not nonzero:
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big_count = len(big_indices)

    # Case 1: all remaining piles are size 1.
    # In misere Nim, positions with an odd number of 1-piles are losing,
    # and positions with an even number are winning. The only legal move
    # is to take one from a size-1 pile.
    if big_count == 0:
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile has size > 1.
    # Reduce it to 0 or 1 so the opponent faces an odd number of 1-piles.
    if big_count == 1:
        i = big_indices[0]
        h = piles[i]

        # If current number of 1-piles is even, leave this big pile as 1.
        # Opponent then has odd number of 1-piles.
        if ones % 2 == 0:
            take = h - 1
            if take >= 1:
                return f"{i},{take}"
            # This fallback is theoretically unreachable because h > 1.
            return f"{i},1"

        # If current number of 1-piles is odd, remove the big pile entirely.
        take = h
        return f"{i},{take}"

    # Case 3: at least two piles have size > 1.
    # Use normal Nim strategy: move to xor zero if possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if take >= 1:
                    return f"{i},{take}"

    # Losing position under perfect play, or no xor move found.
    # Return a legal fallback move. Prefer reducing a large pile slightly,
    # while keeping the move unquestionably legal.
    for i in big_indices:
        return f"{i},1"

    # Final safety fallback: take one from any non-empty pile.
    i = nonzero[0]
    return f"{i},1"
