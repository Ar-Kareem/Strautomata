
def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)

    big = [i for i in range(n) if piles[i] > 1]
    ones = sum(1 for i in range(n) if piles[i] == 1)

    # No big piles: all are 0 or 1. Must take a 1 if available.
    if len(big) == 0:
        for i in range(n):
            if piles[i] >= 1:
                return f"{i},1"
        return "0,1"  # shouldn't happen in a legal state

    # Exactly one pile with size >= 2: misère endgame control.
    if len(big) == 1:
        i = big[0]
        # Leave opponent an odd number of 1-piles.
        if ones % 2 == 0:
            take = piles[i] - 1  # leave one '1' in this pile -> ones+1 (odd)
        else:
            take = piles[i]       # leave zero -> ones (odd)
        if take < 1:
            take = 1
        if take > piles[i]:
            take = piles[i]
        return f"{i},{take}"

    # Standard Nim strategy when at least two piles have size >= 2.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i in range(n):
            target = piles[i] ^ xor_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"

    # Losing position (xor == 0): take 1 from the largest pile.
    i = max(range(n), key=lambda k: piles[k])
    if piles[i] >= 1:
        return f"{i},1"
    # Fallback
    for i in range(n):
        if piles[i] >= 1:
            return f"{i},1"
    return "0,1"
