
def policy(piles: list[int]) -> str:
    # Check if all non-zero piles are of size 1
    all_ones = all(p == 1 for p in piles)
    non_zero_count = sum(1 for p in piles if p > 0)
    
    if all_ones:
        # If the number of non-zero piles is even, current player wins by taking 1 from any pile.
        # If odd, it's a losing position, but we must make a move; take 1 from the first non-zero pile.
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Compute nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum == 0:
        # Losing position: take 1 from the first pile with at least one object.
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Winning move: find a pile where reducing it to (pile XOR nim_sum) is possible.
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # Fallback (should not reach here if there is at least one move)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
