
def policy(piles: list[int]) -> str:
    # Calculate the nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if we're in the endgame (all piles have at most 1 object)
    all_one_or_zero = all(p <= 1 for p in piles)
    
    if all_one_or_zero:
        # Misère endgame: we want to leave an ODD number of piles with 1 object
        # (so opponent is forced to take the last one eventually)
        ones = sum(1 for p in piles if p == 1)
        
        if ones % 2 == 1:
            # Odd number of 1s - we're in a losing position, just take any
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
        else:
            # Even number of 1s - take one to make it odd
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
    
    # Regular Nim strategy with misère adjustment
    if nim_sum == 0:
        # We're in a losing position - make any legal move
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Find a winning move: we want to leave opponent with nim_sum = 0
    # For misère, we also need to consider the endgame
    
    for i, p in enumerate(piles):
        if p == 0:
            continue
        
        # Target value for this pile to make nim_sum = 0
        target = p ^ nim_sum
        
        if target < p:
            take = p - target
            
            # Check if this move leads to endgame
            new_piles = piles.copy()
            new_piles[i] = target
            
            # If resulting position has all piles <= 1, apply misère logic
            if all(np <= 1 for np in new_piles):
                ones = sum(1 for np in new_piles if np == 1)
                # In misère, we want to leave ODD number of 1s
                if ones % 2 == 1:
                    # This is a good move for misère
                    return f"{i},{take}"
                else:
                    # This would be bad for misère, try to find alternative
                    continue
            else:
                # Not endgame, standard nim strategy works
                return f"{i},{take}"
    
    # If no good move found with standard strategy (shouldn't happen often),
    # try any move that leaves odd number of 1s in endgame
    for i, p in enumerate(piles):
        if p > 0:
            for take in range(1, p + 1):
                new_piles = piles.copy()
                new_piles[i] = p - take
                if all(np <= 1 for np in new_piles):
                    ones = sum(1 for np in new_piles if np == 1)
                    if ones % 2 == 1:
                        return f"{i},{take}"
    
    # Fallback: just make any legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    
    # Should never reach here if game state is valid
    return "0,1"
