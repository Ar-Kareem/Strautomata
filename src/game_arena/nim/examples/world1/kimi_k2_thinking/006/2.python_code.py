
def policy(piles):
    """
    Determines the next move for a 4-pile misère Nim game.
    The player who takes the last object loses.
    """
    # Check if all non-zero piles are of size 1 (i.e., no pile > 1)
    if all(p <= 1 for p in piles):
        count_ones = sum(piles)  # total number of non-zero piles (each is 1)
        # If odd number of ones, it's a losing position; if even, it's winning.
        # In both cases, we take one from the first available pile.
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    else:
        # Compute the nim-sum (XOR of all piles)
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        
        if nim_sum == 0:
            # Losing position: make any move (take one from the first non-zero pile)
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
        else:
            # Winning position: find a pile where reducing it makes the nim-sum zero
            for i, p in enumerate(piles):
                if p == 0:
                    continue
                new_p = p ^ nim_sum
                if new_p < p:
                    # Remove (p - new_p) objects from this pile
                    return f"{i},{p - new_p}"
            # Fallback: should not happen, but take one if needed
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
    
    # Fallback for safety: take one from the first non-zero pile
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    # Theoretically unreachable since we are called only when a move exists.
    return "0,0"
