
import numpy as np

def policy(piles: list[int]) -> str:
    """
    Optimal Nim policy implementation.
    
    The strategy is based on the mathematical theory of Nim:
    - If XOR of all pile sizes is 0, the position is losing
    - If XOR is non-zero, we can always make it zero with the right move
    """
    
    # Calculate XOR of all piles
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # If XOR is 0, we're in a losing position - make any legal move
    if xor_sum == 0:
        # Find first non-empty pile and take 1 object
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
    
    # If XOR is non-zero, we can force a winning position
    # Find a pile where we can reduce it to make XOR zero
    for i, pile in enumerate(piles):
        if pile > 0:
            # Calculate what the pile size should be after our move
            target = pile ^ xor_sum
            # If target < pile, we can make this move
            if target < pile:
                take = pile - target
                return f"{i},{take}"
    
    # Fallback (should never reach here with proper implementation)
    # Just take 1 from the first non-empty pile
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
