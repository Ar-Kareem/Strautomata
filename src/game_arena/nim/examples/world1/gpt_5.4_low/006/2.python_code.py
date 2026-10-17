
def policy(piles: list[int]) -> str:
    # Ensure we always return a legal move.
    # piles is expected to be length 4, but this works for any length >= 1.
    
    nonzero = [i for i, x in enumerate(piles) if x > 0]
    if not nonzero:
        # Should not occur in a live game, but return a syntactically valid move.
        return "0,0"

    ones = [i for i, x in enumerate(piles) if x == 1]
    bigs = [i for i, x in enumerate(piles) if x > 1]

    # Case 1: all nonempty piles are size 1
    if len(bigs) == 0:
        # Any move removes exactly one whole pile.
        # Winning iff number of 1-piles is even; remove one to leave odd.
        i = ones[0]
        return f"{i},1"

    # Case 2: exactly one pile is bigger than 1
    if len(bigs) == 1:
        b = bigs[0]
        h = piles[b]
        num_ones = len(ones)

        if num_ones % 2 == 0:
            # Leave an odd number of 1-piles: reduce big heap to 1
            take = h - 1
            if take >= 1:
                return f"{b},{take}"
        else:
            # Leave an odd number of 1-piles by removing the big heap entirely
            take = h
            if take >= 1:
                return f"{b},{take}"

    # Case 3: at least two piles bigger than 1
    # Play normal Nim: move to xor = 0
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

    # Fallback: remove 1 from the first nonempty pile
    i = nonzero[0]
    return f"{i},1"
