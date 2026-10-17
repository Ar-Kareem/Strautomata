
import random

def policy(piles: list[int]) -> str:
    # Calculate XOR of all piles
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # If XOR is zero, we're in a losing position
    # Make a random move
    if xor_sum == 0:
        # Find a non-empty pile
        non_empty_piles = [i for i, pile in enumerate(piles) if pile > 0]
        if non_empty_piles:
            chosen_pile = random.choice(non_empty_piles)
            return f"{chosen_pile},1"
        else:
            # This shouldn't happen in a valid game state
            return "0,1"
    
    # If XOR is non-zero, we can win
    # Find a pile where we can make the XOR zero
    for i, pile in enumerate(piles):
        # Calculate what the pile size should be after our move
        target_size = xor_sum ^ pile
        
        # If target_size is less than current pile size,
        # we can remove objects from this pile
        if target_size < pile:
            take = pile - target_size
            return f"{i},{take}"
    
    # If we got here, there's a bug in our logic
    # Fall back to removing one object from the first non-empty pile
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    
    # This shouldn't happen in a valid game state
    return "0,1"
