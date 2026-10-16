
def policy(piles: list[int]) -> str:
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Count piles with more than 1 object and piles with exactly 1
    large_piles = sum(1 for p in piles if p > 1)
    ones = sum(1 for p in piles if p == 1)
    
    # Find a winning move
    best_move = None
    
    for i in range(4):
        if piles[i] == 0:
            continue
        
        for take in range(1, piles[i] + 1):
            new_piles = piles.copy()
            new_piles[i] -= take
            
            # Calculate new nim-sum
            new_nim_sum = 0
            for p in new_piles:
                new_nim_sum ^= p
            
            # Count large piles and ones after move
            new_large = sum(1 for p in new_piles if p > 1)
            new_ones = sum(1 for p in new_piles if p == 1)
            
            # Misère endgame: if all piles are ≤1 after move, we want odd number of 1s
            if new_large == 0:
                if new_ones % 2 == 1:  # Odd ones means opponent takes last
                    return f"{i},{take}"
            else:
                # Normal play: want nim-sum of 0
                if new_nim_sum == 0:
                    best_move = (i, take)
    
    if best_move:
        return f"{best_move[0]},{best_move[1]}"
    
    # If no winning move found (we're in losing position), make any legal move
    # Prefer smaller takes to prolong game and hope for opponent mistake
    for i in range(4):
        if piles[i] > 0:
            # In losing position, try to complicate things
            # If only one pile, take all but one if possible (unless it's the last object)
            if sum(1 for p in piles if p > 0) == 1:
                if piles[i] > 1:
                    return f"{i},{piles[i] - 1}"
                else:
                    return f"{i},1"
            return f"{i},1"
    
    # Fallback (should never reach here with valid game state)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    return "0,1"
