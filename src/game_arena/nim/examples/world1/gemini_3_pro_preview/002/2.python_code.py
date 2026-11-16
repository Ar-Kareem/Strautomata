
import functools
import operator

def policy(piles: list[int]) -> str:
    """
    Determines the optimal move for Misere Nim (4 piles).
    Returns a string 'pile_index,take_amount'.
    """
    # 1. Calculate the Nim-sum (XOR sum) of the piles
    nim_sum = functools.reduce(operator.xor, piles, 0)
    
    # 2. Identify "large" piles (indices of piles with > 1 object)
    large_piles_indices = [i for i, x in enumerate(piles) if x > 1]
    count_large = len(large_piles_indices)
    
    # 3. Strategy Logic for Misere Play
    
    if count_large == 0:
        # ENDGAME: All piles are size 0 or 1.
        # We must simply take from a pile of size 1.
        # (Optimal play is automatic here: if we have a winning state [even 1s],
        # taking 1 leaves odd 1s for opponent).
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
    
    elif count_large == 1:
        # TRANSITION: Exactly one pile > 1.
        # We control the parity of 1s entering the endgame.
        # We want to leave an ODD number of 1s for the opponent to face.
        idx = large_piles_indices[0]
        
        # Count existing 1s (excluding the large pile)
        num_ones = sum(1 for p in piles if p == 1)
        
        if num_ones % 2 == 0:
            # If even ones exist, we add 1 more '1' (reduce large pile to 1) 
            # to make the total count Odd.
            target_size = 1
        else:
            # If odd ones exist, we add 0 '1's (reduce large pile to 0) 
            # to keep the total count Odd.
            target_size = 0
            
        take = piles[idx] - target_size
        return f"{idx},{take}"
        
    else:
        # NORMAL PLAY: 2 or more large piles.
        # Use Standard Nim strategy (target Nim-sum 0).
        if nim_sum != 0:
            # Winning position: make a move that results in nim_sum 0.
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    # We found the pile to reduce
                    take = p - target
                    return f"{i},{take}"
        else:
            # Losing position (nim_sum is 0).
            # Make a move to complicate the game (take 1 from largest pile).
            max_p = -1
            best_i = 0
            for i, p in enumerate(piles):
                if p > max_p:
                    max_p = p
                    best_i = i
            return f"{best_i},1"

    # Fallback (should not occur with valid positive piles)
    return "0,1"
