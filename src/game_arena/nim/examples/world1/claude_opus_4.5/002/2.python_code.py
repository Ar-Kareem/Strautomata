
def policy(piles: list[int]) -> str:
    # Count piles with objects and piles with more than 1 object
    non_empty = sum(1 for p in piles if p > 0)
    big_piles = sum(1 for p in piles if p > 1)
    
    # Calculate nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Endgame: all non-empty piles have exactly 1 object
    if big_piles == 0:
        # Misère: we want to leave an odd number of piles for opponent
        # So if current non_empty is odd, take 1 (leave even, but opponent takes making it odd-1)
        # If current non_empty is even, take 1 (leave odd for opponent - they lose)
        # We want to leave ODD number of 1-piles for opponent
        # If non_empty is even, taking 1 leaves odd -> good
        # If non_empty is odd, taking 1 leaves even -> opponent leaves odd for us -> bad, but forced
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    # Normal phase: at least one pile has more than 1 object
    # In misère Nim during normal phase, play like normal Nim
    # Try to make nim-sum = 0 (with misère adjustment at transition)
    
    if nim_sum != 0:
        # We can make a winning move
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    # Check misère condition: after this move, check if we enter endgame
                    new_piles = piles.copy()
                    new_piles[i] = target
                    new_big = sum(1 for p in new_piles if p > 1)
                    new_non_empty = sum(1 for p in new_piles if p > 0)
                    
                    if new_big == 0:
                        # We're entering endgame, want to leave odd number of 1s
                        if new_non_empty % 2 == 1:
                            # Good move for misère
                            return f"{i},{take}"
                        else:
                            # Try another option or adjust
                            continue
                    else:
                        # Still in normal phase, this is good
                        return f"{i},{take}"
        
        # If we couldn't find a good misère move, try any move that zeros nim-sum
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
    
    # nim_sum == 0: we're in a losing position, make any legal move
    # Take 1 from the largest pile to minimize damage
    max_pile = -1
    max_idx = -1
    for i in range(4):
        if piles[i] > max_pile:
            max_pile = piles[i]
            max_idx = i
    
    return f"{max_idx},1"
