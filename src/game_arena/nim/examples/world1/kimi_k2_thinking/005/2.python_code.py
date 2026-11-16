
def policy(piles):
    """
    Optimal strategy for 4-pile misère Nim (last move loses).
    Implements the standard misère Nim algorithm:
    - If all piles are size 1: win if even number, lose if odd
    - Otherwise: play like normal Nim, but be careful not to leave 
      an even number of size-1 piles.
    """
    # Safety: if no legal moves (shouldn't happen)
    if not any(p > 0 for p in piles):
        return "0,1"
    
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    max_pile = max(piles)
    
    # Special case: all non-zero piles are size 1
    if max_pile == 1:
        count_ones = sum(piles)
        # Even number of ones: winning position
        if count_ones % 2 == 0:
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
        else:
            # Odd number: losing position (any move is fine)
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
    
    # Losing position in normal Nim (nim_sum == 0)
    if nim_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Winning position: make nim-sum 0 (with misère adjustment)
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            # Simulate the move
            new_piles = piles.copy()
            new_piles[i] = target
            
            # If move leaves only size-1 piles AND an even number of them,
            # this is bad for misère Nim. Take entire pile instead.
            if max(new_piles) <= 1 and sum(new_piles) % 2 == 0:
                return f"{i},{p}"
            
            # Standard winning move
            return f"{i},{p - target}"
    
    # Fallback: shouldn't reach here, but just in case
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
