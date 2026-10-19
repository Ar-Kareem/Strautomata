
def policy(piles: list[int]) -> str:
    # indices of nonzero piles
    nonzero = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        # Should not happen in valid play; return a harmless default
        return "0,0"

    # Count heaps > 1 and heaps == 1
    gt1 = [i for i, p in enumerate(piles) if p > 1]
    ones = [i for i, p in enumerate(piles) if p == 1]

    # Case 1: all nonzero piles are 1
    if len(gt1) == 0:
        # Take one from any pile
        i = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one heap > 1 (special misère rule)
    if len(gt1) == 1:
        i = gt1[0]
        k = piles[i]
        m = len(ones)  # number of size-1 piles
        if m % 2 == 0:
            # leave odd number of ones by reducing to 1
            take = k - 1
        else:
            # leave odd number of ones by removing the heap
            take = k
        return f"{i},{take}"

    # Case 3: normal Nim play
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum == 0:
        # No winning move; take 1 from first nonzero pile
        i = nonzero[0]
        return f"{i},1"

    for i, p in enumerate(piles):
        target = p ^ xor_sum
        if target < p:
            take = p - target
            return f"{i},{take}"

    # Fallback (should not happen)
    i = nonzero[0]
    return f"{i},1"
