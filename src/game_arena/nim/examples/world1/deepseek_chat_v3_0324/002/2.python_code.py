
import numpy as np

def policy(piles: list[int]) -> str:
    # Calculate nim-sum
    nim_sum = np.bitwise_xor.reduce(piles)
    
    # If all piles are size 1, special misère handling
    if all(p == 1 for p in piles):
        # Leave odd number of piles (take from first pile)
        return '0,1'
    
    # Count non-empty piles
    non_empty = sum(1 for p in piles if p > 0)
    
    # When few piles remain, adjust for misère play
    if non_empty <= 2:
        # Find the largest pile (to reduce to 1 or 0)
        max_pile = max((p, i) for i, p in enumerate(piles))[1]
        if piles[max_pile] > 1:
            return f"{max_pile},{piles[max_pile]-1}"
        else:
            # Must take last object from another pile
            for i, p in enumerate(piles):
                if p > 0 and i != max_pile:
                    return f"{i},{p}"
    
    # Standard Nim strategy when not in endgame
    if nim_sum != 0:
        # Find a move that makes nim-sum zero
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    return f"{i},{piles[i] - target}"
    
    # Default move (take from largest pile when in losing position)
    max_pile = max((p, i) for i, p in enumerate(piles))[1]
    return f"{max_pile},1"
