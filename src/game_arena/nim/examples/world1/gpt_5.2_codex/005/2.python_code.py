
def policy(piles: list[int]) -> str:
    # indices of piles
    non_zero = [i for i, p in enumerate(piles) if p > 0]
    if not non_zero:
        # game should be over; return a dummy move
        return "0,0"

    ones = [i for i, p in enumerate(piles) if p == 1]
    big = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all non-zero piles are size 1
    if len(big) == 0:
        idx = ones[0]
        return f"{idx},1"

    # Case 2: exactly one pile > 1
    if len(big) == 1:
        idx = big[0]
        if len(ones) % 2 == 0:
            # make big pile size 1
            take = piles[idx] - 1
            return f"{idx},{take}"
        else:
            # make big pile size 0
            take = piles[idx]
            return f"{idx},{take}"

    # Case 3: at least two piles > 1 -> normal Nim
    s = 0
    for p in piles:
        s ^= p

    if s == 0:
        # no winning move; take 1 from any non-zero pile
        idx = non_zero[0]
        return f"{idx},1"

    # find move to make nim-sum zero
    for i, p in enumerate(piles):
        target = p ^ s
        if target < p:
            take = p - target
            return f"{i},{take}"

    # fallback (should not happen)
    idx = non_zero[0]
    return f"{idx},1"
