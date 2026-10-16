
import sys

def policy(piles: list[int]) -> str:
    # Calculate Nim-sum (XOR of all piles)
    xor_sum = 0
    non_zero_count = 0
    last_non_zero_index = -1
    
    for i, p in enumerate(piles):
        xor_sum ^= p
        if p > 0:
            non_zero_count += 1
            last_non_zero_index = i

    # Misere Nim Strategy:
    
    # 1. Endgame case: Only one pile remains.
    # In Misere Nim, if only one pile is left, you must leave 1 stone for the opponent.
    # So you take (size - 1). If size is 1, you lose (must take 1).
    if non_zero_count == 1:
        pile_idx = last_non_zero_index
        take = piles[pile_idx] - 1
        if take < 1: # Case where pile size is 1
            take = 1 # Forced to take last stone
        return f"{pile_idx},{take}"

    # 2. General case (more than 1 pile).
    # Play standard Nim strategy: If xor_sum != 0, move to make xor_sum 0.
    # If xor_sum == 0, we are in a losing position. We must make a legal move.
    # We choose the move that leaves the opponent with the smallest total stones, 
    # or simply removes 1 from the first pile.
    
    if xor_sum != 0:
        # Find a pile where (pile_size XOR xor_sum) < pile_size
        for i in range(4):
            target = piles[i] ^ xor_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # Fallback for when xor_sum is 0 (losing position) or if logic fails (should not happen)
    # Pick the first non-empty pile and take 1.
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
            
    # This line is theoretically unreachable if called on a non-terminal game state
    return "0,1"
