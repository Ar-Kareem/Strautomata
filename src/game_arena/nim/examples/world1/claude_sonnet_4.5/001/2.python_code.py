
def policy(piles: list[int]) -> str:
    """
    Optimal Nim strategy for misère variant (last player loses).
    Uses XOR-based nim-sum calculation with endgame adjustment.
    """
    
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Check if we're in misère endgame (all non-empty piles have size 1)
    non_zero_piles = [p for p in piles if p > 0]
    in_endgame = all(p <= 1 for p in piles)
    
    if in_endgame:
        # Misère endgame: we want odd number of size-1 piles
        num_ones = sum(1 for p in piles if p == 1)
        if num_ones % 2 == 1:
            # Odd number of 1s - take one to make it even
            for i, pile in enumerate(piles):
                if pile == 1:
                    return f"{i},1"
        else:
            # Even number of 1s (including 0) - shouldn't happen if playing optimally
            # Take from any available pile
            for i, pile in enumerate(piles):
                if pile > 0:
                    return f"{i},{pile}"
    
    # Not in endgame - use standard nim strategy
    if nim_sum != 0:
        # We're in a winning position - find the move that makes nim-sum 0
        for i, pile in enumerate(piles):
            if pile > 0:
                # Calculate what this pile should be to make nim-sum 0
                target = pile ^ nim_sum
                if target < pile:
                    take = pile - target
                    # Verify this doesn't immediately enter bad endgame
                    new_piles = piles[:]
                    new_piles[i] = target
                    
                    # Check if this move creates a losing endgame position
                    if all(p <= 1 for p in new_piles):
                        num_ones = sum(1 for p in new_piles if p == 1)
                        if num_ones % 2 == 0:
                            # This would put us in losing endgame, try another move
                            continue
                    
                    return f"{i},{take}"
    
    # If we're in a losing position (nim-sum = 0) or couldn't find winning move
    # Make a safe move: take 1 from the largest pile
    # Prefer piles with size > 1 to avoid creating endgame
    best_pile = -1
    best_size = 0
    
    for i, pile in enumerate(piles):
        if pile > 1 and pile > best_size:
            best_size = pile
            best_pile = i
    
    if best_pile != -1:
        return f"{best_pile},1"
    
    # No pile with size > 1, take from any non-empty pile
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    
    # Fallback (should never reach here)
    return "0,1"
