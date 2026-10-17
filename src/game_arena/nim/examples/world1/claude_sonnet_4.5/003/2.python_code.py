
def policy(piles: list[int]) -> str:
    """
    Optimal misère Nim strategy for 4 piles.
    Player who takes the last object loses.
    """
    
    # Check if we're in endgame (all piles are 0 or 1)
    all_small = all(pile <= 1 for pile in piles)
    
    if all_small:
        # Endgame: count piles with exactly 1 object
        ones_count = sum(1 for pile in piles if pile == 1)
        
        # We want to leave an odd number of 1s for opponent
        # If currently even number of 1s, take one to make it odd
        # If currently odd, this shouldn't happen in optimal play from start
        
        for pile_idx in range(4):
            if piles[pile_idx] == 1:
                # Taking this would change parity
                if ones_count % 2 == 0:
                    # Even number of 1s - take one to leave odd
                    return f"{pile_idx},1"
        
        # Shouldn't reach here in normal play, but return any legal move
        for pile_idx in range(4):
            if piles[pile_idx] > 0:
                return f"{pile_idx},{piles[pile_idx]}"
    
    else:
        # Normal play: use Nim-sum strategy
        nim_sum = 0
        for pile in piles:
            nim_sum ^= pile
        
        if nim_sum == 0:
            # Already in losing position, make any legal move
            # Prefer taking 1 from largest pile to avoid entering endgame badly
            for pile_idx in range(4):
                if piles[pile_idx] > 0:
                    return f"{pile_idx},1"
        
        # Find a move that makes nim_sum = 0
        for pile_idx in range(4):
            if piles[pile_idx] > 0:
                # What should this pile be to make nim_sum = 0?
                target = nim_sum ^ piles[pile_idx]
                
                if target < piles[pile_idx]:
                    # We can reduce this pile to target
                    take = piles[pile_idx] - target
                    
                    # Verify this move doesn't create bad endgame
                    new_piles = piles[:]
                    new_piles[pile_idx] = target
                    
                    # Check if this creates endgame
                    if all(p <= 1 for p in new_piles):
                        ones = sum(1 for p in new_piles if p == 1)
                        # We want odd number of 1s for opponent
                        if ones % 2 == 1:
                            return f"{pile_idx},{take}"
                    else:
                        # Not endgame, safe to make this move
                        return f"{pile_idx},{take}"
        
        # Fallback: shouldn't reach here, but return any legal move
        for pile_idx in range(4):
            if piles[pile_idx] > 0:
                return f"{pile_idx},1"
    
    # Final fallback
    return "0,1"
