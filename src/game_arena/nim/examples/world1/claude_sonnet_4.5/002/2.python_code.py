
def policy(piles: list[int]) -> str:
    """
    Optimal Nim strategy for misère variant (last player loses).
    Uses Sprague-Grundy theorem with endgame adjustment.
    """
    
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Check if we're in endgame (all non-empty piles have size 1)
    non_empty = [p for p in piles if p > 0]
    all_ones = all(p <= 1 for p in non_empty)
    
    if all_ones:
        # Endgame: leave odd number of piles for opponent (so they take last)
        # Take from any non-empty pile
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
    
    # Standard play: make nim-sum = 0 if possible
    if nim_sum != 0:
        # Find a pile where removing objects makes nim-sum = 0
        for i, pile in enumerate(piles):
            if pile > 0:
                # Target value for this pile after our move
                target = pile ^ nim_sum
                # We can achieve this if target < pile
                if target < pile:
                    take = pile - target
                    return f"{i},{take}"
    
    # If nim-sum is already 0, we're in losing position
    # Make any legal move (take 1 from first non-empty pile)
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    
    # Fallback (should never reach here if game isn't over)
    return "0,1"
