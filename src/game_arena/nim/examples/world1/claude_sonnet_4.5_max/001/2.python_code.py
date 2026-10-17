
def policy(piles: list[int]) -> str:
    """
    Optimal strategy for Misère Nim (4 piles).
    
    In Misère Nim, the player who takes the last object loses.
    
    A position is a P-position (losing position) if and only if:
    1. All piles ≤ 1 and there's an odd number of piles with exactly 1 object, OR
    2. At least one pile > 1 and the nim-sum (XOR of all piles) equals 0.
    
    Strategy: Move to a P-position if possible, otherwise make any legal move.
    """
    
    def is_losing_position(state):
        """Check if a state is a P-position (losing position)."""
        large_piles = sum(1 for p in state if p > 1)
        
        if large_piles == 0:
            # Endgame: all piles have at most 1 object
            ones = sum(1 for p in state if p == 1)
            return ones % 2 == 1  # Lose if odd number of 1s
        else:
            # Not endgame: at least one pile has more than 1 object
            nim_sum = 0
            for p in state:
                nim_sum ^= p
            return nim_sum == 0  # Lose if nim-sum is 0
    
    # Check if current position is in endgame
    large_piles = sum(1 for p in piles if p > 1)
    
    if large_piles == 0:
        # Endgame: outcome is predetermined, just make any legal move
        for i in range(len(piles)):
            if piles[i] > 0:
                return f"{i},1"
    
    # Not in endgame: try to find a move to a P-position
    
    # Calculate nim-sum of current position
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Strategy 1: Try standard Nim move (reduce a pile to make nim-sum = 0)
    if nim_sum != 0:
        for i in range(len(piles)):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    new_piles = piles[:]
                    new_piles[i] = target
                    if is_losing_position(new_piles):
                        return f"{i},{piles[i] - target}"
    
    # Strategy 2: Try to enter endgame with odd number of 1s
    for i in range(len(piles)):
        if piles[i] > 1:
            for new_value in [1, 0]:
                new_piles = piles[:]
                new_piles[i] = new_value
                if is_losing_position(new_piles):
                    return f"{i},{piles[i] - new_value}"
    
    # No winning move exists (we're in a P-position)
    # Make any legal move
    for i in range(len(piles)):
        if piles[i] > 0:
            return f"{i},1"
    
    # Fallback (should never reach here in a valid game)
    return "0,1"
