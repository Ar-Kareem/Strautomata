
def policy(piles: list[int]) -> str:
    """
    Determines the optimal move for Misere Nim (4 piles).
    Returns a string 'pile_index,take_amount'.
    """
    # 1. Calculate the Nim-sum (XOR sum) of the piles
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # 2. Identify heavy piles (size > 1)
    # We need to distinguish between endgame scenarios and normal play
    large_piles_indices = [i for i, x in enumerate(piles) if x > 1]
    count_large = len(large_piles_indices)
    
    # --- STRATEGY IMPLEMENTATION ---

    # Case A: Endgame - Only piles of size 0 or 1 remain.
    # Goal: Leave the opponent with an ODD number of 1s.
    if count_large == 0:
        ones_indices = [i for i, x in enumerate(piles) if x == 1]
        # Whether the current count is even or odd, taking 1 from a pile of size 1
        # is the only move that makes progress.
        # If Count is Even (Winning): Taking 1 leaves Odd (Goal).
        # If Count is Odd (Losing): Taking 1 leaves Even.
        if ones_indices:
            return f"{ones_indices[0]},1"

    # Case B: Exactly one pile is larger than 1.
    # Goal: Force the endgame state with an ODD number of 1s.
    elif count_large == 1:
        idx = large_piles_indices[0]
        # Count 1s in the other piles
        other_ones_count = sum(1 for i, x in enumerate(piles) if x == 1 and i != idx)
        
        # We need Total 1s to be Odd.
        # If others are Even, we need this pile to become 1.
        # If others are Odd, we need this pile to become 0.
        if other_ones_count % 2 == 0:
            target_size = 1
        else:
            target_size = 0
            
        take = piles[idx] - target_size
        return f"{idx},{take}"

    # Case C: Two or more piles larger than 1.
    # Goal: Play Normal Nim strategy (reduce Nim-sum to 0).
    else:
        # If Nim-sum is non-zero, we can move to a winning state (Sum = 0)
        if nim_sum != 0:
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    take = p - target
                    return f"{i},{take}"
        
        # If Nim-sum is 0, we are in a losing position.
        # We just play a legal move (take 1 from biggest pile) to prolong the game.
        max_idx = -1
        max_val = -1
        for i, p in enumerate(piles):
            if p > max_val:
                max_val = p
                max_idx = i
        return f"{max_idx},1"

    # Fallback for safety (though logic above covers all valid game states with objects)
    return "0,1"
