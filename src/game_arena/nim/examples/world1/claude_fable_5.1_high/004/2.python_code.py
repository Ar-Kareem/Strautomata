
def policy(piles: list[int]) -> str:
    n = len(piles)
    nonzero = [i for i in range(n) if piles[i] > 0]
    if not nonzero:
        return "0,1"  # game already over; fallback

    big = [i for i in range(n) if piles[i] >= 2]
    ones = sum(1 for p in piles if p == 1)

    # Case: all piles are 0 or 1 -> just take one object
    if len(big) == 0:
        return f"{nonzero[0]},1"

    # Case: exactly one pile >= 2 -> leave odd number of ones
    if len(big) == 1:
        i = big[0]
        if ones % 2 == 0:
            # leave this pile as 1 -> ones becomes odd
            return f"{i},{piles[i] - 1}"
        else:
            # remove pile entirely -> ones stays odd
            return f"{i},{piles[i]}"

    # Case: >= 2 big piles -> normal Nim strategy
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
    # Losing position: stall by taking 1 from the largest pile
    imax = max(range(n), key=lambda i: piles[i])
    return f"{imax},1"
