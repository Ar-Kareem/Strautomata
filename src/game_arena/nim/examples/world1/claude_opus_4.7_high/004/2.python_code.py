
def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)
    big = [i for i in range(n) if piles[i] > 1]
    nonzero = [i for i in range(n) if piles[i] > 0]

    # Safety: if nothing to take (shouldn't happen in a live game)
    if not nonzero:
        return "0,1"

    # Case 1: all piles are 0 or 1
    if len(big) == 0:
        # Forced move; take one from any nonzero pile
        return f"{nonzero[0]},1"

    # Case 2: exactly one pile > 1
    if len(big) == 1:
        i = big[0]
        ones = sum(1 for j in nonzero if j != i)
        # We want to leave opponent facing an odd number of 1-piles
        if ones % 2 == 0:
            # leave a single 1 in this pile => ones+1 (odd)
            take = piles[i] - 1
        else:
            # take the whole pile => ones (odd)
            take = piles[i]
        if take < 1:
            take = 1
        if take > piles[i]:
            take = piles[i]
        return f"{i},{take}"

    # Case 3: two or more piles > 1, play normal Nim (misère reduces to normal here)
    x = 0
    for p in piles:
        x ^= p

    if x == 0:
        # Losing position; make a minimal move from a big pile
        return f"{big[0]},1"

    # Find a pile where p ^ x < p
    for i, p in enumerate(piles):
        if (p ^ x) < p:
            take = p - (p ^ x)
            if 1 <= take <= p:
                return f"{i},{take}"

    # Fallback (should not reach here)
    return f"{nonzero[0]},1"
