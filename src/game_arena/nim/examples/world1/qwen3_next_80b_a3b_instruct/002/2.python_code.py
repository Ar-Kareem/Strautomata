
import numpy as np

def policy(piles: list[int]) -> str:
    # Count number of piles greater than 1
    large_count = sum(1 for p in piles if p > 1)
    ones_count = sum(1 for p in piles if p == 1)
    
    # Case 1: All piles are 0 or 1 (i.e., no large piles)
    if large_count == 0:
        # We have 4 piles total, some are 0, some are 1. We need to take one object from a pile of 1.
        # Find any pile with 1 and take it all.
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
        # If no pile is 1? (shouldn't happen since large_count=0 and not all zero)
        # Take from first non-zero pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Case 2: Exactly one pile > 1
    elif large_count == 1:
        # Find the large pile index
        big_idx = -1
        for i in range(4):
            if piles[i] > 1:
                big_idx = i
                break
        # If we have even number of ones, reduce big pile to 1
        if ones_count % 2 == 0:
            take = piles[big_idx] - 1
            return f"{big_idx},{take}"
        else:
            # Reduce big pile to 0
            take = piles[big_idx]
            return f"{big_idx},{take}"
    
    # Case 3: Two or more piles > 1
    else:
        # Compute nim-sum
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        
        # If nim-sum is 0, we're in a losing position. We need to make any legal move.
        if nim_sum == 0:
            # Find first non-zero pile and take 1 (minimal move)
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
            # All zero? shouldn't happen
            return "0,1"
        
        # Otherwise, find a move that makes nim_sum = 0
        for i in range(4):
            if piles[i] == 0:
                continue
            # What should be the new size of pile i to make nim_sum 0?
            new_size = piles[i] ^ nim_sum
            if new_size < piles[i]:  # We can reduce this pile to new_size
                take = piles[i] - new_size
                return f"{i},{take}"
        
        # If we didn't find a move? Shouldn't happen due to Nim theory.
        # Fallback: take one from first non-zero pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
        
        return "0,1"  # This should never be reached
   