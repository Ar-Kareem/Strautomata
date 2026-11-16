
def policy(piles: list[int]) -> str:
    """
    Optimal policy for misère Nim (4 piles).
    The player who takes the last object loses.
    
    Strategy:
    - If all piles are size 1: Leave an odd number of piles for opponent
    - If only one pile > 1: Make all piles size 1 with even count
    - If multiple piles > 1: Use XOR strategy for optimal move
    """
    # Count piles of size 1 and piles > 1
    ones = sum(1 for p in piles if p == 1)
    big = sum(1 for p in piles if p > 1)
    
    # Case 1: All piles are size 1
    if big == 0:
        # Need to leave odd number of piles (1, 3, 5, ...)
        # If current count is even, leave 3; if odd, leave 1
        target_ones = 3 if ones % 2 == 0 else 1
        take = ones - target_ones
        if take > 0:
            # Find a pile with 1 stone and take it
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
        return "0,1"  # Fallback
    
    # Case 2: Only one pile > 1 (special case)
    if big == 1:
        # Find the big pile
        big_idx = None
        for i, p in enumerate(piles):
            if p > 1:
                big_idx = i
                break
        
        # Goal: Leave all piles as size 1 with even count
        # This means we need even number of 1s after our move
        # If current ones is odd, we want even (keep big as 1)
        # If current ones is even, we want odd (keep big as >1)
        
        if ones % 2 == 0:
            # Current ones is even, want odd -> leave big as size 1
            take = piles[big_idx] - 1
            return f"{big_idx},{take}"
        else:
            # Current ones is odd, want even -> leave big as size > 1
            # Can we make XOR=0? Only if big pile can be reduced to make XOR=0
            xor = 0
            for p in piles:
                xor ^= p
            # Try to make XOR=0
            for i, p in enumerate(piles):
                if i == big_idx:
                    target = xor ^ p
                    if target < p:
                        take = p - target
                        return f"{i},{take}"
            # Fallback: take all but 1
            return f"{big_idx},{piles[big_idx] - 1}"
    
    # Case 3: Multiple piles > 1 (use standard Nim strategy)
    # Find a move that makes XOR = 0
    xor = 0
    for p in piles:
        xor ^= p
    
    if xor != 0:
        for i, p in enumerate(piles):
            target = xor ^ p
            if target < p:
                take = p - target
                return f"{i},{take}"
    
    # Fallback: take 1 from first non-empty pile
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    
    return "0,1"  # Should never reach here if game is ongoing
