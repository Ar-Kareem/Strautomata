
def policy(piles: list[int]) -> str:
    # Count piles
    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]

    # If all piles are size 1
    if len(big_indices) == 0:
        # Take one from any nonzero pile
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # If exactly one pile is larger than 1
    if len(big_indices) == 1:
        i = big_indices[0]
        k = ones
        # Leave opponent with odd number of size-1 heaps
        if k % 2 == 0:
            # Reduce big heap to 1
            take = piles[i] - 1
        else:
            # Remove big heap entirely
            take = piles[i]
        return f"{i},{take}"

    # Otherwise play normal Nim
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum == 0:
        # No winning move, take 1 from first nonzero pile
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    else:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                return f"{i},{take}"

    # Fallback (should never be reached)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
