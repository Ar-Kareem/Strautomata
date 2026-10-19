
import functools
import operator

def policy(piles: list[int]) -> str:
    """
    Calculates the optimal move for Misere Nim (last player to move loses).
    """
    # Calculate Nim-sum (XOR of all pile sizes)
    nim_sum = functools.reduce(operator.xor, piles, 0)
    
    # Count piles of size 1 and piles greater than 1 to handle the Misere endgame
    num_ones = sum(1 for p in piles if p == 1)
    num_large = sum(1 for p in piles if p > 1)
    
    # If Nim-sum is not 0, we can force a win with optimal play
    if nim_sum != 0:
        for i, p in enumerate(piles):
            if p == 0:
                continue
            
            # Calculate the target size for this pile to make Nim-sum 0
            target = p ^ nim_sum
            
            # A valid move must reduce the pile size
            if target < p:
                take = p - target
                
                # Misere Endgame Exception:
                # If this move leaves no piles > 1, we are entering the endgame.
                # Standard Nim strategy aims for Nim-sum 0, which implies an EVEN number
                # of size-1 piles in the endgame. In Misere, we want an ODD number
                # of size-1 piles to force the opponent to take the last object.
                
                is_last_large_pile = (p > 1) and (num_large == 1)
                
                if is_last_large_pile and target <= 1:
                    # Calculate how many ones will be left
                    # 'p' is currently large, so it contributes 0 to num_ones.
                    # If target is 1, it contributes 1. If 0, it contributes 0.
                    future_ones = num_ones + (1 if target == 1 else 0)
                    
                    if future_ones % 2 == 0:
                        # We are about to leave an even number of 1s. This is losing in Misere.
                        # We must adjust the move to leave an odd number of 1s.
                        if target == 1:
                            # Instead of leaving 1, leave 0 (take 1 more)
                            take += 1
                        elif target == 0:
                            # Instead of leaving 0, leave 1 (take 1 less)
                            take -= 1
                
                return f"{i},{take}"
    
    # Fallback for losing positions (Nim-sum is 0) or theoretical safety
    # Take 1 from the first available pile (prefer taking from large piles to complicate opponent's task)
    for i, p in enumerate(piles):
        if p > 1:
            return f"{i},1"
    
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
            
    return "0,1"
