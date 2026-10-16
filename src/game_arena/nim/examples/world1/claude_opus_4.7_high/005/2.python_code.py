
def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)
    big = [i for i in range(n) if piles[i] > 1]
    ones = [i for i in range(n) if piles[i] == 1]

    # All piles are 0 or 1
    if len(big) == 0:
        if ones:
            return f"{ones[0]},1"
        # Fallback (shouldn't be reached in a live game)
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,1"

    # Exactly one "big" pile (size >= 2)
    if len(big) == 1:
        b = big[0]
        m = len(ones)
        # We want to leave opponent with an ODD number of 1-piles total.
        if m % 2 == 0:
            # leave 1 in the big pile -> total ones = m+1 (odd)
            take = piles[b] - 1
        else:
            # take everything in the big pile -> total ones = m (odd)
            take = piles[b]
        if take < 1:
            take = 1
        if take > piles[b]:
            take = piles[b]
        return f"{b},{take}"

    # Two or more big piles: play normal Nim (XOR strategy)
    xor_val = 0
    for p in piles:
        xor_val ^= p

    if xor_val == 0:
        # Losing position; make a minimal move to prolong the game
        return f"{big[0]},1"

    # Find a pile we can reduce to p ^ xor_val
    for i, p in enumerate(piles):
        if p == 0:
            continue
        target = p ^ xor_val
        if target < p:
            take = p - target
            if 1 <= take <= p:
                return f"{i},{take}"

    # Fallback
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    return "0,1"
