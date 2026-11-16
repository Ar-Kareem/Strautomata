
def policy(piles: list[int]) -> str:
    # Count piles with more than 1 object
    count_greater_than_one = sum(1 for p in piles if p > 1)
    
    # Case 1: all piles are 0 or 1 (but game ends when all zero, so at least one non-zero)
    if count_greater_than_one == 0:
        # All piles are 1 (since game is ongoing, at least one is 1)
        # Take one object from the first non-zero pile (any pile with 1)
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Case 2: exactly one pile has more than 1
    elif count_greater_than_one == 1:
        # Find the pile with more than 1
        for i in range(4):
            if piles[i] > 1:
                # Since there are 3 piles of 1 (odd number), we take the entire pile
                # This leaves 3 piles of 1 (odd) which is a losing position for opponent
                return f"{i},{piles[i]}"
    
    # Case 3: two or more piles have more than 1
    else:
        # Compute nim-sum (XOR of all piles)
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        
        # If nim_sum is 0, we are in a losing position, but must make a move
        # Take 1 from the first non-zero pile
        if nim_sum == 0:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        
        # Else: nim_sum != 0, find a pile to reduce to make nim_sum 0
        for i in range(4):
            if piles[i] == 0:
                continue
            # Target size for pile i after move
            target = piles[i] ^ nim_sum
            # We can reduce pile i if target < piles[i]
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # Fallback: should not reach here because game state must be non-terminal and have at least one non-zero pile
    # But to be safe: take one from first non-zero pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
