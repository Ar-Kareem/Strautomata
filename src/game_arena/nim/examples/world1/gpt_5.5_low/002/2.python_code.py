
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Defensive normalization: ensure we only work with integer pile sizes.
    piles = [int(x) for x in piles]

    # Find all non-empty piles for a guaranteed legal fallback.
    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # This should not be called on a terminal state, but return something
    # syntactically valid if it ever is.
    if not nonzero:
        return "0,0"

    # Count piles with more than one object.
    big = [i for i, p in enumerate(piles) if p > 1]
    ones = sum(1 for p in piles if p == 1)

    # Case 1: all piles are size 0 or 1.
    # In misere Nim, odd number of ones is losing, even number is winning.
    # The only legal move is to remove one from a pile with one object.
    if len(big) == 0:
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile has more than one object.
    # Reduce it to 0 or 1 so that the opponent faces an odd number of ones.
    if len(big) == 1:
        i = big[0]
        pile_size = piles[i]

        # Choose remaining amount r in {0, 1} such that ones + r is odd.
        # If ones is even, leave r = 1.
        # If ones is odd, leave r = 0.
        remaining = 1 if ones % 2 == 0 else 0
        take = pile_size - remaining

        # Since pile_size > 1 and remaining is 0 or 1, take is always legal.
        return f"{i},{take}"

    # Case 3: at least two piles are greater than one.
    # Use normal Nim xor strategy.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    # If xor is nonzero, move to xor zero.
    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if take >= 1:
                    return f"{i},{take}"

    # Losing position or unexpected edge case: return a legal fallback.
    # Prefer taking one from the largest pile.
    i = max(nonzero, key=lambda idx: piles[idx])
    return f"{i},1"
