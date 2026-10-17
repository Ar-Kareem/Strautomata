
def policy(piles: list[int]) -> str:
    non_zero = [i for i, p in enumerate(piles) if p > 0]
    if len(non_zero) == 1:
        pile = non_zero[0]
        return f"{pile},{piles[pile] - 1}"
    
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum == 0:
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        for i in range(4):
            if piles[i] > 0:
                desired = piles[i] ^ nim_sum
                take = piles[i] - desired
                if take > 0 and take <= piles[i]:
                    return f"{i},{take}"
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Fallback (should never be reached with valid input)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
