
def policy(piles: list[int]) -> str:
    piles = list(piles)
    
    # Case 1: All piles are 1
    if all(p == 1 for p in piles):
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    non_ones = [p for p in piles if p > 1]
    ones_count = sum(1 for p in piles if p == 1)
    
    # Case 2: Exactly one non-one pile
    if len(non_ones) == 1:
        idx = piles.index(non_ones[0])
        if ones_count % 2 == 0:
            return f"{idx},{non_ones[0] - 1}"
        else:
            return f"{idx},{non_ones[0]}"
    
    # Case 3: Compute nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim_sum is zero (losing position), take from largest pile
    if nim_sum == 0:
        max_pile = max(piles)
        for i in reversed(range(4)):
            if piles[i] == max_pile:
                return f"{i},1"
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Try to find safe nim-sum move
    for i in range(4):
        if piles[i] > 0:
            target = piles[i] ^ nim_sum
            if target >= piles[i]: 
                continue
            take = piles[i] - target
            new_piles = piles.copy()
            new_piles[i] = target
            new_non_zero = [p for p in new_piles if p > 0]
            if (all(p == 1 for p in new_non_zero) and 
                len(new_non_zero) % 2 == 0):
                continue  # Skip bad moves
            return f"{i},{take}"
    
    # Fallback strategies
    for i in range(4):
        if piles[i] > 1:
            new_non_zero = [p for j, p in enumerate(piles) if j != i and p > 0]
            if (all(p == 1 for p in new_non_zero) and 
                len(new_non_zero) % 2 == 1):
                return f"{i},{piles[i]}"
    
    for i in range(4):
        if piles[i] > 1:
            take = piles[i] - 1
            new_piles = piles.copy()
            new_piles[i] = 1
            new_non_zero = [p for p in new_piles if p > 0]
            if (all(p == 1 for p in new_non_zero) and 
                len(new_non_zero) % 2 == 1):
                return f"{i},{take}"
    
    # Final fallback: take first available
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    # Should never reach here (all piles empty)
    return "0,1"
