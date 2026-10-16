
import sys

def policy(piles: list[int]) -> str:
    """
    Calculates the optimal move for Misère Nim (4 piles).
    Returns a string 'pile,take'.
    """
    # Calculate the Nim-sum (XOR of all pile sizes)
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    # Identify indices of "large" piles (size >= 2)
    # In Misère Nim, the strategy changes when no piles are >= 2.
    large_piles_indices = [i for i, x in enumerate(piles) if x >= 2]
    num_large = len(large_piles_indices)
    
    # Determine if we are in a losing position
    # Losing if: (Regular play and nim_sum == 0) OR (Endgame and nim_sum == 1)
    is_losing = False
    if num_large > 0:
        if nim_sum == 0:
            is_losing = True
    else:
        # Endgame: only 0s and 1s.
        # Nim_sum 1 means odd number of 1s. In Misère, this is a losing position.
        if nim_sum == 1:
            is_losing = True
            
    # If in a losing position, we must make a legal move.
    # We take 1 from the first available pile. The opponent must play perfectly to win.
    if is_losing:
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
    
    # Winning Position Strategy
    
    # Case 1: Endgame (No piles >= 2)
    # We are here only if nim_sum == 0 (even number of 1s).
    # Strategy: Take 1 to make the count of 1s odd (nim_sum 1).
    if num_large == 0:
        for i, x in enumerate(piles):
            if x == 1:
                return f"{i},1"
    
    # Case 2: Exactly one large pile
    # We are transitioning into the endgame.
    # Standard Nim strategy would make nim_sum 0 (even number of 1s total).
    # In Misère, we want to leave the opponent with an ODD number of 1s.
    # Let k be the count of size-1 piles.
    # If we reduce the large pile to 0 -> total 1s = k.
    # If we reduce the large pile to 1 -> total 1s = k + 1.
    # We choose the option that results in an odd total.
    elif num_large == 1:
        idx_large = large_piles_indices[0]
        val_large = piles[idx_large]
        
        # Count piles of size 1
        k = sum(1 for x in piles if x == 1)
        
        # We want the resulting number of 1s to be odd.
        # If k is odd, we want to leave 0 in the large pile (total k).
        # If k is even, we want to leave 1 in the large pile (total k+1).
        
        if k % 2 == 1:
            # Leave 0 in the large pile
            take = val_large
        else:
            # Leave 1 in the large pile
            take = val_large - 1
            
        return f"{idx_large},{take}"
        
    # Case 3: Multiple large piles (Regular Nim strategy)
    # We simply make the move that sets the Nim-sum to 0.
    # Find a pile x where (x XOR nim_sum) < x.
    else:
        for i, x in enumerate(piles):
            target = x ^ nim_sum
            if target < x:
                take = x - target
                return f"{i},{take}"
    
    # Fallback: Should not be reached if logic above is correct
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"
            
    return "0,0"
