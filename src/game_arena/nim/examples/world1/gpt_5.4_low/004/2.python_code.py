
def policy(piles: list[int]) -> str:
    # Collect nonempty piles
    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # Terminal state should normally not be queried, but guard anyway.
    if not nonzero:
        return "0,0"

    ones = [i for i, p in enumerate(piles) if p == 1]
    bigs = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all nonempty piles are size 1
    if len(bigs) == 0:
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one pile larger than 1
    if len(bigs) == 1:
        i = bigs[0]
        m = len(ones)
        target = 1 if (m % 2 == 0) else 0
        take = piles[i] - target
        if 1 <= take <= piles[i]:
            return f"{i},{take}"

    # Case 3: at least two piles larger than 1 -> normal Nim move
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Safe fallback: return any legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    # Unreachable unless all piles are zero
    return "0,0"
