
import functools
import operator

def policy(piles: list[int]) -> str:
    # Calculate nim-sum (binary XOR of all piles)
    nim_sum = functools.reduce(operator.xor, piles)
    
    # Check if all piles are size 1 (misère endgame)
    if all(pile <= 1 for pile in piles):
        # Odd number of 1's - must take last one (losing position)
        # We can make opponent take last by taking whole pile
        # Or minimize damage by taking from largest pile if possible
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},{pile}"
    
    # Normal Nim strategy - find move that makes nim-sum zero
    for i, pile in enumerate(piles):
        if pile == 0:
            continue
        target_size = pile ^ nim_sum
        if target_size < pile:
            take = pile - target_size
            return f"{i},{take}"
    
    # Fallback: if no optimal move found, take from largest pile
    max_pile = max(piles)
    for i, pile in reversed(list(enumerate(piles))):
        if pile == max_pile and pile > 0:
            return f"{i},1"
    
    # Default move (should never reach here in valid game states)
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    return "0,1"  # failsafe
