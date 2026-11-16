
def policy(piles: list[int]) -> str:
    n = len(piles)
    
    # Calculate XOR of all piles
    xor_sum = 0
    for p in piles:
        xor_sum ^= p
    
    # Check if we're in endgame (all piles have at most 1 object)
    max_pile = max(piles)
    
    if max_pile <= 1:
        # Endgame: all piles are 0 or 1
        # We want to leave an odd number of 1s (so opponent takes last)
        ones = sum(piles)
        if ones % 2 == 0:
            # Even 1s - we're in losing position, just take one
            for i in range(n):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # Odd 1s - we're winning, take one to leave even for opponent
            for i in range(n):
                if piles[i] == 1:
                    return f"{i},1"
    
    # Normal Nim strategy with Misère adjustment
    # Try to make xor_sum = 0 after our move
    
    for i in range(n):
        if piles[i] == 0:
            continue
        
        target = piles[i] ^ xor_sum
        if target < piles[i]:
            take = piles[i] - target
            
            # Check resulting state
            new_piles = piles.copy()
            new_piles[i] -= take
            
            # Check if this leaves endgame position
            new_max = max(new_piles)
            if new_max <= 1:
                # Endgame reached - need odd number of 1s remaining
                ones_left = sum(new_piles)
                if ones_left % 2 == 1:
                    # Good - odd 1s left, opponent will take last
                    return f"{i},{take}"
                else:
                    # Bad - try to adjust by taking one more or one less if possible
                    if take + 1 <= piles[i]:
                        # Take one more (if pile[i] was going to be 1, now it's 0)
                        return f"{i},{take + 1}"
                    elif take > 1:
                        # Take one less
                        return f"{i},{take - 1}"
                    # else this move is bad, try other piles
            else:
                # Not endgame, standard Nim strategy works
                return f"{i},{take}"
    
    # No winning move found (we're in a losing position)
    # Make a move that might complicate things for opponent
    # Prefer taking from largest pile
    best_pile = -1
    best_size = 0
    for i in range(n):
        if piles[i] > best_size:
            best_size = piles[i]
            best_pile = i
    
    if best_pile >= 0:
        # Take 1 from the largest pile (conservative)
        return f"{best_pile},1"
    
    # Fallback: find any legal move
    for i in range(n):
        if piles[i] > 0:
            return f"{i},1"
    
    # Should never reach here if game state is valid
    return "0,1"
