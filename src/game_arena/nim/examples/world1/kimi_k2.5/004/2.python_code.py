
def policy(piles: list[int]) -> str:
    """
    Optimal misère Nim strategy for 4 piles.
    Returns move as 'pile_index,amount_to_take'.
    """
    ones_count = 0
    big_indices = []  # indices with piles > 1
    
    for i, p in enumerate(piles):
        if p == 1:
            ones_count += 1
        elif p > 1:
            big_indices.append(i)
    
    # Case 1: No big piles (only 0s and 1s remain)
    if not big_indices:
        # Take any available 1
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # Should not reach here (no legal move), but return valid format
        return "0,0"
    
    # Case 2: Exactly one pile > 1
    if len(big_indices) == 1:
        idx = big_indices[0]
        p = piles[idx]
        if ones_count % 2 == 0:
            # Leave odd number of ones: make big pile into 1
            # Take p-1 (valid since p >= 2)
            return f"{idx},{p - 1}"
        else:
            # Leave odd number of ones: make big pile into 0
            return f"{idx},{p}"
    
    # Case 3: Two or more piles > 1 - play normal Nim
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If losing position, make arbitrary move
    if nim_sum == 0:
        idx = big_indices[0]
        return f"{idx},1"
    
    # Find winning move: reduce a pile to (pile XOR nim_sum)
    for i, p in enumerate(piles):
        if p > 0:
            target = p ^ nim_sum
            if target < p:
                take = p - target
                return f"{i},{take}"
    
    # Fallback (should not reach here)
    idx = big_indices[0]
    return f"{idx},1"
