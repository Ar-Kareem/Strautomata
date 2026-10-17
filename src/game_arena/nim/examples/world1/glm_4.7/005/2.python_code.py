
from functools import reduce

def policy(piles: list[int]) -> str:
    # Helper to check if a hypothetical state is a losing state for the NEXT player (i.e., P-position)
    def is_p_position(state):
        max_pile = max(state)
        if max_pile <= 1:
            # In Misère Endgame, P-position if the number of 1s is odd
            return sum(state) % 2 == 1
        else:
            # In Standard play, P-position if Nim-sum is 0
            return reduce(lambda x, y: x ^ y, state) == 0

    # 1. Handle Endgame directly (simple parity logic)
    if max(piles) <= 1:
        # If even number of 1s, we are winning. Take 1 to make it odd.
        # If odd number of 1s, we are losing. Any move (taking 1) is standard.
        # Just find the first pile with a stone.
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # 2. Standard Play (at least one pile > 1)
    nim_sum = reduce(lambda x, y: x ^ y, piles)

    # Generate candidate moves
    # Candidates include:
    # a) The move that makes nim_sum 0 (Standard Nim strategy)
    # b) Reducing the largest pile to 0 or 1 (for the Misère edge case)
    candidates = []
    
    for i, p in enumerate(piles):
        # Strategy a: Move to make XOR 0
        target = p ^ nim_sum
        if target < p:
            candidates.append((i, p - target))
        
        # Strategy b: Reduce to 0 (if pile > 0)
        if p > 0:
            candidates.append((i, p - 0))
        
        # Strategy c: Reduce to 1 (if pile > 1)
        if p > 1:
            candidates.append((i, p - 1))

    # Evaluate candidates to find a move to a P-position
    for pile_idx, take in candidates:
        new_piles = list(piles)
        new_piles[pile_idx] -= take
        
        # Verify legality
        if new_piles[pile_idx] < 0:
            continue
            
        if is_p_position(new_piles):
            return f"{pile_idx},{take}"

    # 3. Fallback (if no winning move found or in losing state)
    # If we are in a losing state (nim_sum == 0), we return a safe move.
    # Heuristic: Take 1 from the largest pile.
    max_val = max(piles)
    for i, p in enumerate(piles):
        if p == max_val:
            return f"{i},1"
            
    # Ultimate fallback (should not be reached)
    return "0,1"
