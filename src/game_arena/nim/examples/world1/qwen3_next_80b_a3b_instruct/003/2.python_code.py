
import numpy as np

def policy(piles: list[int]) -> str:
    # Count how many piles have more than 1 item
    count_greater_than_one = sum(1 for p in piles if p > 1)
    
    # Case 1: All piles are 1
    if count_greater_than_one == 0:
        # We have [1,1,1,1]. Take 1 from any pile (e.g., the first) to leave 3 ones (odd)
        return "0,1"
    
    # Compute nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Case 2: nim_sum != 0 and there's at least one pile > 1
    # We want to make a move to set nim_sum to 0
    if nim_sum != 0:
        for i in range(4):
            # We want to reduce pile i to piles[i] ^ nim_sum
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                if take >= 1:
                    return f"{i},{take}"
    
    # Case 3: nim_sum == 0 (losing position) but there's at least one pile > 1
    # We must make a move. Best is to take 1 from the largest pile to avoid giving opponent a simple path
    # Find the pile with the most objects
    max_pile = max(piles)
    for i in range(4):
        if piles[i] == max_pile:
            # Take 1 from the largest pile
            return f"{i},1"
    
    # Fallback: should never reach here, but guarantee a legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
