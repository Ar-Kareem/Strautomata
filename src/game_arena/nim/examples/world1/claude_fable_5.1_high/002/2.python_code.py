
def policy(piles: list[int]) -> str:
    n = len(piles)
    big = [i for i in range(n) if piles[i] >= 2]
    ones = sum(1 for p in piles if p == 1)

    # Case 1: all piles are 0 or 1
    if len(big) == 0:
        for i in range(n):
            if piles[i] >= 1:
                return f"{i},1"
        return "0,1"  # should never happen (game over)

    # Case 2: exactly one pile >= 2 -> leave an odd number of ones
    if len(big) == 1:
        i = big[0]
        if ones % 2 == 0:
            take = piles[i] - 1   # leave this pile at 1 -> odd number of ones
        else:
            take = piles[i]       # remove pile -> odd number of ones remains
        take = max(1, min(take, piles[i]))
        return f"{i},{take}"

    # Case 3: two or more piles >= 2 -> normal Nim
    x = 0
    for p in piles:
        x ^= p
    if x != 0:
        for i in range(n):
            target = piles[i] ^ x
            if target < piles[i]:
                take = piles[i] - target
                if 1 <= take <= piles[i]:
                    return f"{i},{take}"

    # Losing position (or fallback): take 1 from the largest pile
    idx = max(range(n), key=lambda i: piles[i])
    if piles[idx] >= 1:
        return f"{idx},1"
    for i in range(n):
        if piles[i] >= 1:
            return f"{i},1"
    return "0,1"
