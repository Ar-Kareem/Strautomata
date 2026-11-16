
import numpy as np

def policy(piles: list[int]) -> str:
    """
    Returns a move in the format 'pile,take' based on the Nim strategy.
    """
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if nim_sum == 0:
        # If nim_sum is 0, make a random legal move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
        # If all piles are zero, return some default string, although it should not happen.
        return "0,0"  

    else:
        # Find a pile to reduce to make the nim_sum 0
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                
                # Check if only one pile has objects and the nim_sum is one.
                non_zero_piles = np.count_nonzero(piles)
                if non_zero_piles == 1 and nim_sum == 1:
                    take = piles[i] - 1
                    return f"{i},{take}"              
                else:
                    return f"{i},{take}"

    return "0,1" # Should not happen, but included to ensure a valid return
