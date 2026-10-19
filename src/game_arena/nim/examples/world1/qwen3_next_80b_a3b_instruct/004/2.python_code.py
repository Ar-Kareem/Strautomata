
def policy(piles: list[int]) -> str:
    # Count the number of piles with exactly 1
    ones = sum(1 for p in piles if p == 1)
    if ones == 4:
        # All are ones: take one from the first pile
        return "0,1"
    
    # Calculate nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    if nim_sum == 0:
        # Losing position: take 1 from the largest pile
        # Find the largest pile (iterate from last index to first to get the first occurrence of max)
        max_val = max(piles)
        for i in range(4):
            if piles[i] == max_val:
                return f"{i},1"
    else:
        # Winning position: find a move to make nim_sum 0
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
    
    # Fallback: should not happen
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
