
import functools
import operator

def policy(piles: list[int]) -> str:
    """
    Determines the optimal move for Misere Nim (4 piles).
    Returns a string 'pile,take'.
    """
    # Calculate the Nim-sum (XOR sum) of all piles
    nim_sum = functools.reduce(operator.xor, piles, 0)
    
    # Identify piles that are larger than 1
    large_piles_indices = [i for i, size in enumerate(piles) if size > 1]
    num_large = len(large_piles_indices)
    
    # --- Strategy Logic ---
    
    # Case 1: Misere Endgame Transition (Exactly one pile > 1)
    # The standard Nim strategy (XOR sum 0) fails here in Misere play.
    # We must force the game into a state with an ODD number of 1s.
    if num_large == 1:
        pile_idx = large_piles_indices[0]
        pile_size = piles[pile_idx]
        
        # Count piles that are exactly size 1.
        # Note: piles.count(1) counts all 1s. Since pile_size > 1, it is not counted here.
        num_ones = piles.count(1)
        
        if num_ones % 2 == 0:
            # Existing 1s count is even. We need to add one 1 to make total odd.
            # Reduce the large pile to size 1.
            take = pile_size - 1
            return f"{pile_idx},{take}"
        else:
            # Existing 1s count is odd. We need to leave them as is (total remains odd).
            # Remove the large pile entirely (reduce to 0).
            take = pile_size
            return f"{pile_idx},{take}"

    # Case 2: Standard Play (2 or more piles > 1)
    # Play like Standard Nim: try to reach a state with Nim-sum 0.
    # With >= 2 large piles, moving to XOR 0 cannot result in exactly 1 large pile,
    # so we don't need to worry about the Misere exception yet.
    elif num_large >= 2:
        if nim_sum != 0:
            # Winning position: find a move that makes nim_sum 0
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    take = p - target
                    return f"{i},{take}"
        
        # If nim_sum is already 0, we are in a losing position (against optimal play).
        # We must make a legal move. Taking 1 from the largest pile is a reasonable heuristic.
        max_p = -1
        max_i = -1
        for i, p in enumerate(piles):
            if p > max_p:
                max_p = p
                max_i = i
        return f"{max_i},1"
            
    # Case 3: All piles are size 0 or 1
    # The game is primarily decided. We just make the first legal move available.
    else:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Fail-safe (should not be reached if input represents a game still in progress)
    return "0,1"
