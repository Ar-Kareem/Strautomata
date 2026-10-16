
def policy(piles: list[int]) -> str:
    # Ensure length 4 assumption is handled robustly
    n = len(piles)

    # Collect pile categories
    nonzero = [i for i, x in enumerate(piles) if x > 0]
    ones = [i for i, x in enumerate(piles) if x == 1]
    big = [i for i, x in enumerate(piles) if x > 1]

    # No legal move exists in a terminal state, but return a syntactically valid default.
    # Arena should not call policy on terminal states.
    if not nonzero:
        return "0,0"

    # Misère Nim special handling

    # Case 1: all nonzero piles are size 1
    if len(big) == 0:
        # Optimal: leave an odd number of 1-heaps to opponent.
        # If count is even, remove one to make it odd.
        # If count is odd, no winning move exists; remove one legally.
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile larger than 1
    if len(big) == 1:
        i = big[0]
        ones_count = len(ones)
        target = 1 if (ones_count % 2 == 1) else 0
        take = piles[i] - target
        if take >= 1:
            return f"{i},{take}"

    # Case 3: at least two piles larger than 1
    # Play normal Nim: make xor zero
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

    # Fallback: always return a legal move
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"

    # Unreachable unless terminal
    return "0,0"
