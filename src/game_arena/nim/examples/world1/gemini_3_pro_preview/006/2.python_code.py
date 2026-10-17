
import functools
import operator

def policy(piles: list[int]) -> str:
    # Identify indices of piles that have more than 1 item
    large_piles_indices = [i for i, x in enumerate(piles) if x > 1]
    
    # CASE 1: Exactly one pile has more than 1 item.
    # This is the critical adjustment for Misere Nim. We can control the usage of the 
    # large pile to ensure the remaining game consists purely of 1s, and we want 
    # the count of those 1s to be ODD.
    if len(large_piles_indices) == 1:
        idx = large_piles_indices[0]
        pile_size = piles[idx]
        
        # Count only the piles that are already size 1
        ones_count = piles.count(1)
        
        # If the number of existing 1s is even, we need the large pile to become 1 
        # (total 1s = even + 1 = odd).
        if ones_count % 2 == 0:
            take = pile_size - 1
        # If the number of existing 1s is odd, we need the large pile to become 0 
        # (total 1s = odd + 0 = odd).
        else:
            take = pile_size
            
        return f"{idx},{take}"

    # CASE 2: Standard Strategy (0 or >=2 large piles).
    # We attempt to make the Nim-sum (XOR sum) zero.
    nim_sum = functools.reduce(operator.xor, piles, 0)
    
    if nim_sum != 0:
        # Find the pile and the amount to take to zero out the nim_sum
        for i, val in enumerate(piles):
            # Target size = current size XOR nim_sum
            target = val ^ nim_sum
            if target < val:
                take = val - target
                return f"{i},{take}"
    
    # CASE 3: No winning move available (Nim-sum is 0).
    # We must make a legal move. We take 1 from the first available pile.
    for i, val in enumerate(piles):
        if val > 0:
            return f"{i},1"
            
    # Fallback (should not be reached if game is active)
    return "0,1"
