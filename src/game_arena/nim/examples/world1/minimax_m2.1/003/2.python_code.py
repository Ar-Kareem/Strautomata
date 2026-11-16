
def policy(piles: list[int]) -> str:
    """
    Determine the optimal move in a 4-pile Misère Nim game.
    
    Misère Nim Strategy:
    1. If all piles are size 1: Control parity (leave even number of piles for opponent)
    2. Otherwise: Use XOR strategy to maintain winning position
    
    Args:
        piles: List of 4 integers representing pile sizes
        
    Returns:
        String in format 'pile,take' representing the optimal move
    """
    
    # Check if game is over (all piles zero)
    if all(p == 0 for p in piles):
        return "0,0"  # No moves available
    
    # Count piles with size 1
    count_ones = sum(1 for p in piles if p == 1)
    
    # Strategy 1: All piles are size 1 (endgame)
    if count_ones == 4:
        # Take 1 from a pile to leave odd number (3) for opponent
        # They will be forced to leave even, and eventually take last
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Strategy 2: Mixed pile sizes (midgame) - use XOR strategy
    # Calculate XOR of all piles
    xor_sum = 0
    for p in piles:
        xor_sum ^= p
    
    # If XOR is 0, we're in losing position - make any legal move
    if xor_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                # Take all from a pile with size > 1 if possible
                if p > 1:
                    return f"{i},{p}"
                # Otherwise take 1 from a size-1 pile
                return f"{i},1"
    
    # If XOR is non-zero, we can force a win - find winning move
    # Find a pile where p > (p XOR xor_sum) to make the move
    for i, p in enumerate(piles):
        target = p ^ xor_sum  # The value this pile should become
        if target < p:
            take = p - target
            if 1 <= take <= p:
                return f"{i},{take}"
    
    # Fallback (should never reach here if logic is correct)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
