
def policy(piles: list[int]) -> str:
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Count piles with more than 1 object and piles with exactly 1
    piles_gt_1 = sum(1 for p in piles if p > 1)
    piles_eq_1 = sum(1 for p in piles if p == 1)
    
    # Endgame: all non-empty piles have size 1
    if piles_gt_1 == 0:
        # We want to leave an ODD number of piles (so opponent takes last)
        # Currently there are piles_eq_1 piles of size 1
        # If piles_eq_1 is even, we lose (take 1, leave odd for opponent who then leaves even)
        # If piles_eq_1 is odd, we win (take 1, leave even for opponent)
        # Either way, just take 1 from any pile of size 1
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
    
    # If only one pile > 1, we're about to enter endgame
    if piles_gt_1 == 1:
        # Find the pile > 1
        for i, p in enumerate(piles):
            if p > 1:
                # After our move, we want odd number of piles of size 1
                # Currently there are piles_eq_1 piles of size 1
                # If we take all from pile i: piles_eq_1 remains, want it odd
                # If we leave 1 in pile i: piles_eq_1 + 1, want it odd
                if piles_eq_1 % 2 == 0:
                    # Leave 1, so total size-1 piles = piles_eq_1 + 1 (odd)
                    take = p - 1
                else:
                    # Take all, so total size-1 piles = piles_eq_1 (odd)
                    take = p
                return f"{i},{take}"
    
    # Standard nim strategy: try to make nim_sum = 0
    if nim_sum == 0:
        # We're in a losing position, make any legal move
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Find a pile where we can reduce to make nim_sum = 0
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            # Check if this move leads to endgame
            new_piles = piles.copy()
            new_piles[i] = target
            new_gt_1 = sum(1 for x in new_piles if x > 1)
            new_eq_1 = sum(1 for x in new_piles if x == 1)
            
            if new_gt_1 == 0:
                # We're entering endgame, need odd number of 1s
                if new_eq_1 % 2 == 1:
                    return f"{i},{take}"
                # Otherwise, try another move or adjust
                else:
                    continue
            else:
                return f"{i},{take}"
    
    # Fallback: if no good move found, make any legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
