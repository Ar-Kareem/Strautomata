
def policy(piles: list[int]) -> str:
    """
    Optimal Nim strategy for misère variant (last player to move loses).
    """
    
    def nim_sum(piles):
        """Calculate XOR of all pile values."""
        result = 0
        for pile in piles:
            result ^= pile
        return result
    
    def is_endgame(piles):
        """Check if all non-empty piles have exactly 1 object."""
        return all(pile <= 1 for pile in piles)
    
    current_nim_sum = nim_sum(piles)
    
    # Endgame strategy: all piles are 0 or 1
    if is_endgame(piles):
        # Count non-empty piles
        non_empty = sum(1 for pile in piles if pile > 0)
        
        # We want to leave an odd number of piles for opponent
        # (so they take the last object)
        if non_empty % 2 == 0:
            # Even number of piles - take one to make it odd
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Odd number of piles - take one to make it even
            # (this is a losing move but unavoidable)
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    
    # Normal play: try to make nim_sum = 0 for opponent
    if current_nim_sum != 0:
        # Winning position - find move that makes nim_sum = 0
        for pile_idx in range(4):
            if piles[pile_idx] > 0:
                # Calculate target pile size
                target = piles[pile_idx] ^ current_nim_sum
                
                # Check if this gives us a valid move
                if target < piles[pile_idx]:
                    take = piles[pile_idx] - target
                    
                    # Verify this move makes nim_sum = 0
                    new_piles = piles.copy()
                    new_piles[pile_idx] = target
                    
                    if nim_sum(new_piles) == 0:
                        return f"{pile_idx},{take}"
    
    # Losing position (nim_sum already 0) or no winning move found
    # Make any legal move, preferring to take 1 from largest pile
    for pile_idx in range(4):
        if piles[pile_idx] > 0:
            # Try taking 1 from this pile
            return f"{pile_idx},1"
    
    # Fallback (should never reach here if game state is valid)
    return "0,1"
