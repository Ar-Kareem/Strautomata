
def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)

    def legal(p, t):
        return 0 <= p < n and 1 <= t <= piles[p]

    big = [i for i in range(n) if piles[i] > 1]
    ones = sum(1 for v in piles if v == 1)

    # Case 1: all piles are 0 or 1 -> only possible move is take 1 from a nonempty pile
    if not big:
        for i in range(n):
            if piles[i] >= 1:
                return f"{i},1"
        return "0,1"  # no legal move exists (game over); fallback

    # Case 2: exactly one pile > 1 -> leave an odd number of 1-piles
    if len(big) == 1:
        i = big[0]
        if ones % 2 == 1:
            take = piles[i]        # remove whole pile -> odd ones remain
        else:
            take = piles[i] - 1    # leave 1 -> odd ones remain
        if legal(i, take):
            return f"{i},{take}"

    # Case 3: at least two piles > 1 -> normal Nim strategy
    x = 0
    for v in piles:
        x ^= v
    if x != 0:
        for i in range(n):
            target = piles[i] ^ x
            if target < piles[i]:
                take = piles[i] - target
                if legal(i, take):
                    return f"{i},{take}"

    # Losing position (or fallback): take 1 from the largest pile to stall
    i = max(range(n), key=lambda k: piles[k])
    if legal(i, 1):
        return f"{i},1"
    for k in range(n):
        if piles[k] >= 1:
            return f"{k},1"
    return "0,1"
