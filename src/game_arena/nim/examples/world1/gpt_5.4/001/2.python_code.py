
def policy(piles: list[int]) -> str:
    # Always return a legal move string "pile,take".
    # Misère Nim optimal strategy for 4 piles.

    # Safety: find all non-empty piles
    nonzero = [i for i, x in enumerate(piles) if x > 0]
    if not nonzero:
        # Should not normally be called on terminal states, but stay safe.
        return "0,0"

    ones = sum(1 for x in piles if x == 1)
    big = [(i, x) for i, x in enumerate(piles) if x > 1]

    # Case 1: all nonzero piles are size 1
    if len(big) == 0:
        # Winning move iff number of 1-heaps is even:
        # remove one whole heap, leaving odd count to opponent.
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile bigger than 1
    if len(big) == 1:
        i, x = big[0]
        # In misère Nim, leave opponent with:
        # - odd number of ones if we reduce big pile to 0 when ones even
        # - odd number of ones if we reduce big pile to 1 when ones odd
        target = 1 if (ones % 2 == 1) else 0
        take = x - target
        if 1 <= take <= x:
            return f"{i},{take}"

    # Case 3: at least two piles > 1 => normal Nim move
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

    # Losing position or any unexpected issue: return first legal move
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"

    # Final safety fallback
    return "0,0"
