
def policy(piles: list[int]) -> str:
    # Check if all piles are exactly 1
    all_ones = all(p == 1 for p in piles)
    if all_ones:
        # If all piles are 1, take one from the first pile (any pile would work)
        # This ensures the opponent is left with an odd number of piles if original count was even.
        return "0,1"
    
    # Calculate the nim-sum of the piles
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim-sum is non-zero, find a move to set it to zero
    if nim_sum != 0:
        for i in range(4):
            if piles[i] == 0:
                continue
            desired = piles[i] ^ nim_sum
            if desired < piles[i]:
                return f"{i},{piles[i] - desired}"
    
    # If nim-sum is zero (no winning move in normal play), take 1 from the first non-empty pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
