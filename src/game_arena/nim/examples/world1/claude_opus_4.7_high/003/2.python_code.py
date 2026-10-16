
def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)
    big = [i for i in range(n) if piles[i] >= 2]
    ones = sum(1 for p in piles if p == 1)

    # All piles are 0 or 1
    if len(big) == 0:
        for i in range(n):
            if piles[i] >= 1:
                return f"{i},1"
        # shouldn't happen
        return "0,1"

    # Exactly one pile with >= 2 objects
    if len(big) == 1:
        i = big[0]
        # After move, pile i becomes 0 or 1. We want opponent to face an odd number of 1-piles.
        if ones % 2 == 0:
            # Leave pile i as 1 -> total ones becomes ones+1 (odd)
            take = piles[i] - 1
            if take < 1:
                take = 1  # safety
            return f"{i},{take}"
        else:
            # Leave pile i as 0 -> total ones stays odd
            return f"{i},{piles[i]}"

    # At least two piles with >= 2 objects: standard Nim XOR strategy
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i in range(n):
            target = piles[i] ^ xor_sum
            if target < piles[i]:
                return f"{i},{piles[i] - target}"

    # Losing position (xor == 0) or fallback: take 1 from largest pile
    i = max(range(n), key=lambda x: piles[x])
    if piles[i] >= 1:
        return f"{i},1"
    for i in range(n):
        if piles[i] >= 1:
            return f"{i},1"
    return "0,1"
