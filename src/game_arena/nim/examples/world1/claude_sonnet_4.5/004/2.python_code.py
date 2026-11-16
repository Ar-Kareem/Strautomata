
def policy(piles: list[int]) -> str:
    """
    Optimal policy for misère Nim (4 piles).
    Taking the last object loses.
    """
    
    # Calculate Nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Check if we're in endgame (all non-empty piles have size 1)
    non_empty_piles = [p for p in piles if p > 0]
    in_endgame = all(p <= 1 for p in non_empty_piles)
    
    if in_endgame:
        # Endgame strategy: leave odd number of piles for opponent
        num_piles = len(non_empty_piles)
        
        if num_piles % 2 == 1:
            # Odd number of piles - take one to leave even
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Even number - we're losing, take any pile
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    
    else:
        # Normal Nim strategy: move to make Nim-sum = 0
        if nim_sum != 0:
            # We're in a winning position, find the winning move
            for i in range(4):
                if piles[i] > 0:
                    # Try to find a move that makes nim_sum = 0
                    target = piles[i] ^ nim_sum
                    if target < piles[i]:
                        take = piles[i] - target
                        # Check if this leaves us in proper endgame state
                        new_piles = piles.copy()
                        new_piles[i] = target
                        
                        # Verify this is a valid winning move
                        return f"{i},{take}"
        else:
            # We're in a losing position, make a reasonable move
            # Take from largest pile, but carefully
            max_pile_idx = -1
            max_pile_size = 0
            for i in range(4):
                if piles[i] > max_pile_size:
                    max_pile_size = piles[i]
                    max_pile_idx = i
            
            if max_pile_idx != -1:
                # Take 1 from the largest pile
                return f"{max_pile_idx},1"
    
    # Fallback: take 1 from first non-empty pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    # Emergency fallback (should never reach here)
    return "0,1"
