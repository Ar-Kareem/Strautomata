
import numpy as np

def policy(piles: list[int]) -> str:
    # Check for immediate winning moves
    for i in range(4):
        if piles[i] > 0:
            # Try taking all but 1 from this pile
            if piles[i] > 1:
                # Count non-empty piles after this move
                non_empty = sum(1 for j in range(4) if j != i and piles[j] > 0) + 1  # +1 for this pile left with 1
                if non_empty % 2 == 1:  # Odd number of non-empty piles is winning in misère
                    return f"{i},{piles[i]-1}"
            
            # Try taking all from this pile
            non_empty = sum(1 for j in range(4) if j != i and piles[j] > 0)
            if non_empty > 0 and non_empty % 2 == 1:
                return f"{i},{piles[i]}"
    
    # Calculate nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim-sum is zero, we're in a losing position - play to leave odd piles
    if nim_sum == 0:
        # Find the largest pile and reduce it appropriately
        max_pile = max(piles)
        max_idx = piles.index(max_pile)
        
        # Count non-empty piles
        non_empty = sum(1 for p in piles if p > 0)
        
        if max_pile == 1:
            # All piles are 1, take from any pile
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # Reduce largest pile to create odd number of non-empty piles
            if non_empty % 2 == 0:
                # Need odd, so reduce to 1
                return f"{max_idx},{max_pile-1}"
            else:
                # Already odd, reduce to 0
                return f"{max_idx},{max_pile}"
    
    # Nim-sum is non-zero, find a move to make it zero
    for i in range(4):
        if piles[i] > 0:
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                return f"{i},{piles[i] - target}"
    
    # Fallback - should not reach here in optimal play
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    return "0,1"  # Default fallback
