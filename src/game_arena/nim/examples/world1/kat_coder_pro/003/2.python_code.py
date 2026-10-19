
from typing import List

def policy(piles: List[int]) -> str:
    # Calculate XOR of all piles
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # If XOR is 0, we're in a losing position, make a safe move
    if xor_sum == 0:
        # Find the first non-empty pile and remove 1 object
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
    
    # Try to find a pile where we can make the XOR zero
    for i, pile in enumerate(piles):
        if pile > 0:
            # Calculate what the new pile size should be
            new_size = pile ^ xor_sum
            # If the new size is smaller than the current size, we can make this move
            if new_size < pile:
                return f"{i},{pile - new_size}"
    
    # Fallback (should not happen in a winning position)
    # Find the first non-empty pile and remove 1 object
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
