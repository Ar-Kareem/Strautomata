
def policy(piles: list[int]) -> str:
    """
    Optimal Nim strategy for misère play (last player loses).
    """
    
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Check if we're in endgame (all non-empty piles have size 1)
    non_empty = [p for p in piles if p > 0]
    is_endgame = all(p <= 1 for p in non_empty)
    
    if is_endgame:
        # In endgame, we want to leave an even number of piles (odd for opponent to take last)
        num_piles = len(non_empty)
        # Leave odd number of piles so opponent faces even and eventually takes last
        if num_piles % 2 == 1:
            # Take one pile
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # This shouldn't happen if we played optimally, but take any pile
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},{piles[i]}"
    
    # Check if move would create endgame with all piles <= 1
    def creates_bad_endgame(pile_idx, take_amount):
        new_piles = piles.copy()
        new_piles[pile_idx] -= take_amount
        non_empty_after = [p for p in new_piles if p > 0]
        if all(p <= 1 for p in non_empty_after):
            # We're creating endgame - check if it's good for us
            num_piles_after = len(non_empty_after)
            # We want to leave even number of singleton piles
            return num_piles_after % 2 == 1
        return False
    
    if nim_sum == 0:
        # We're in a losing position, make any legal move avoiding bad endgames
        for i in range(4):
            if piles[i] > 0:
                for take in range(piles[i], 0, -1):
                    if not creates_bad_endgame(i, take):
                        return f"{i},{take}"
        # If all moves create bad endgames, take from largest pile
        max_pile = max(range(4), key=lambda i: piles[i])
        return f"{max_pile},{piles[max_pile]}"
    
    # We're in a winning position - find the optimal move
    # Standard Nim: reduce a pile to make nim_sum = 0
    for i in range(4):
        if piles[i] > 0:
            # Target value for this pile
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                # Check if this creates a bad endgame
                if not creates_bad_endgame(i, take):
                    return f"{i},{take}"
    
    # Fallback: should not reach here in optimal play, but make any legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    # Ultimate fallback (should never reach here)
    return "0,1"
