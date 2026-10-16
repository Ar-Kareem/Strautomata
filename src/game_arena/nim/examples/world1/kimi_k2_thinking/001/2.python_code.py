
def policy(piles: list[int]) -> str:
    # Find a default move first
    for i, p in enumerate(piles):
        if p > 0:
            default_move = f"{i},1"
            break
    else:
        # Should not happen in a valid game state
        return "0,0"
    
    # Check for all-ones position (all non-zero piles are size 1)
    non_zero = [p for p in piles if p > 0]
    if len(non_zero) > 0 and all(p == 1 for p in non_zero):
        # Even number of ones = winning, odd = losing
        if len(non_zero) % 2 == 0:
            # Winning position: take an entire pile
            return default_move
        else:
            # Losing position: any move
            return default_move
    
    # Calculate nim-sum for normal Nim strategy
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum == 0:
        # Losing position: any legal move
        return default_move
    
    # Find a winning move (make nim-sum zero)
    for i, p in enumerate(piles):
        if p > 0:
            target = p ^ nim_sum
            if target < p:
                take = p - target
                return f"{i},{take}"
    
    # Fallback (shouldn't happen)
    return default_move
