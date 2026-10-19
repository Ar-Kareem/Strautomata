
def policy(piles: list[int]) -> str:
    """
    Optimal strategy for misère Nim with 4 piles.
    Uses XOR sum to find winning moves, with special handling for
    endgame positions where all non-empty piles have size 1.
    """
    # Calculate Nim sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Count piles with size > 1
    piles_gt_1 = sum(1 for p in piles if p > 1)
    # Count piles with size == 1
    piles_eq_1 = sum(1 for p in piles if p == 1)
    
    # If all piles are 0 or 1, we're in the endgame
    if piles_gt_1 == 0:
        # In misère Nim with only 1s, we want to leave an odd number of 1s
        # (so opponent takes the last one)
        # Current number of 1s is piles_eq_1
        # If odd, we want to take 1 from any pile of size 1 (leaving even)
        # If even, we want to take the last object from a pile of size 1 (leaving odd)
        # Wait, let's think again:
        # If there are k piles of size 1, and it's our turn:
        # - If k is odd: we want to take 1 from a pile, leaving k-1 (even) piles of 1
        #   Then opponent faces even number of 1s and eventually takes the last one
        # - If k is even: we want to take the last object from a pile (i.e., take 1, 
        #   removing that pile), leaving k-1 (odd) piles of 1
        #   Then opponent faces odd number and will eventually take the last one
        # Actually, in misère Nim with only 1s:
        # Normal Nim: player who takes last wins. With only 1s, XOR sum = k mod 2.
        # Misère: player who takes last loses.
        # With only 1s, the losing positions are when k mod 2 == 1 (odd number of 1s)
        # Because if 1 pile of 1, you must take it and lose.
        # If 2 piles of 1, you take 1, leave 1, opponent takes it and loses.
        # So winning move: if piles_eq_1 is even, take 1 from a pile of size 1
        # If piles_eq_1 is odd... wait, if it's odd, you're in a losing position.
        # But we must make a legal move. Any move loses against perfect play.
        # We'll just take 1 from a pile of size 1 if available, or take from any pile.
        if piles_eq_1 > 0:
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
        # If somehow no piles of 1 but all <= 1 (all zeros), game should be over
        # Just return any valid move (shouldn't happen)
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},{p}"
        return "0,0"  # fallback
    
    # Normal misère strategy: use XOR sum, but be careful near the end
    # If xor_sum is 0, we're in a losing position; make any move that doesn't
    # immediately lose and hope opponent makes a mistake
    if nim_sum == 0:
        # Make a move that doesn't create a losing endgame if possible
        # Just take 1 from the largest pile as a safe default
        max_pile_idx = max(range(4), key=lambda i: piles[i])
        return f"{max_pile_idx},1"
    
    # Find a move that makes nim_sum zero
    for i, p in enumerate(piles):
        if p > 0:
            # We want to reduce pile i to p ^ nim_sum
            target = p ^ nim_sum
            if target < p:
                take = p - target
                # Check if this move would leave a position with no piles > 1
                # and an even number of piles of size 1 (which is losing in misère)
                new_piles = piles.copy()
                new_piles[i] = target
                new_gt_1 = sum(1 for x in new_piles if x > 1)
                new_eq_1 = sum(1 for x in new_piles if x == 1)
                
                if new_gt_1 == 0 and new_eq_1 % 2 == 1:
                    # This would leave a losing endgame position for the opponent
                    # (odd number of 1s is losing in misère with only 1s)
                    return f"{i},{take}"
                elif new_gt_1 > 0:
                    # Normal winning move
                    return f"{i},{take}"
                # If new_gt_1 == 0 and new_eq_1 is even, this move makes us lose
                # Skip it and look for another winning move
    
    # If we get here, all winning XOR moves lead to a bad endgame
    # We need to adjust: instead of making xor_sum 0, make a move that
    # leaves exactly one pile > 1, and an odd number of 1s
    for i, p in enumerate(piles):
        if p > 1:
            for take in range(1, p + 1):
                new_piles = piles.copy()
                new_piles[i] = p - take
                new_gt_1 = sum(1 for x in new_piles if x > 1)
                new_eq_1 = sum(1 for x in new_piles if x == 1)
                if new_gt_1 == 1 and new_eq_1 % 2 == 0:
                    return f"{i},{take}"
    
    # Fallback: make any legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    
    return "0,0"
