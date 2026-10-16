
def policy(piles: list[int]) -> str:
    # Compute nim-sum of all piles
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Count piles with size > 1 (large piles)
    large_count = sum(1 for p in piles if p > 1)
    
    # Helper function to check if a state is a P-position (losing for player to move)
    def is_p_position(state):
        # Count piles > 1
        state_large = sum(1 for p in state if p > 1)
        if state_large == 0:
            # All piles are 0 or 1: P-position if odd number of 1's
            ones = sum(1 for p in state if p == 1)
            return ones % 2 == 1
        else:
            # At least one pile > 1: P-position if nim-sum is 0
            x = 0
            for p in state:
                x ^= p
            return x == 0
    
    # Search for a winning move: one that leads to a P-position
    for i, p in enumerate(piles):
        if p == 0:
            continue
        
        # 1. Try the standard Nim move (if it exists)
        target = p ^ nim_sum
        if target < p:
            new_piles = piles.copy()
            new_piles[i] = target
            if is_p_position(new_piles):
                return f"{i},{p - target}"
        
        # 2. If there's only one large pile, also check:
        #    - Clearing the pile (take all)
        #    - Leaving one object (take p-1)
        if large_count == 1 and p > 1:
            # Try clearing the pile
            new_piles = piles.copy()
            new_piles[i] = 0
            if is_p_position(new_piles):
                return f"{i},{p}"
            
            # Try leaving exactly one object
            if p > 1:
                new_piles = piles.copy()
                new_piles[i] = 1
                if is_p_position(new_piles):
                    return f"{i},{p - 1}"
    
    # If no winning move found (we're in a P-position), make any legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
