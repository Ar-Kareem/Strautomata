
def policy(piles: list[int]) -> str:
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile

    if xor_sum != 0:
        for i in range(4):
            p = piles[i]
            desired = p ^ xor_sum
            if desired < p:
                take = p - desired
                return f"{i},{take}"

    all_ones = all(p == 1 for p in piles)
    if all_ones:
        return "0,1"  # All piles are 1s; even count allows you to win
    else:
        for i in range(4):
            if piles[i] > 1:
                take = piles[i] - 1
                return f"{i},{take}"
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"

    # Fallback for cases not handled (should never reach here)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"
