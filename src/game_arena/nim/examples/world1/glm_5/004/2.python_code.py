
def policy(piles: list[int]) -> str:
    """
    Compute the next move for misère Nim (4 piles).
    The player who takes the last object loses.
    """
    n = len(piles)
    
    # Identify big piles (> 1) and count ones
    big_piles = [(i, p) for i, p in enumerate(piles) if p > 1]
    ones = sum(1 for p in piles if p == 1)
    
    if len(big_piles) == 1:
        # Exactly one pile > 1: special misère strategy
        # Leave all piles <= 1 with odd number of 1s
        i, x = big_piles[0]
        k = ones  # number of other piles with size 1
        if k % 2 == 1:
            # Leave k ones (odd): reduce big pile to 0
            return f"{i},{x}"
        else:
            # Leave k+1 ones (odd): reduce big pile to 1
            return f"{i},{x - 1}"
    
    elif len(big_piles) >= 2:
        # Standard Nim XOR strategy with misère adjustment
        xor_val = 0
        for p in piles:
            xor_val ^= p
        
        if xor_val != 0:
            # N-position: find winning move to make XOR = 0
            for i in range(n):
                if piles[i] > 0:
                    target = piles[i] ^ xor_val
                    if target < piles[i]:
                        take = piles[i] - target
                        new_piles = list(piles)
                        new_piles[i] = target
                        new_big_piles = sum(1 for p in new_piles if p > 1)
                        
                        if new_big_piles == 0:
                            # Misère adjustment: ensure odd number of 1s
                            new_ones = sum(1 for p in new_piles if p == 1)
                            if new_ones % 2 == 1:
                                return f"{i},{take}"
                            elif target == 1:
                                # Take one more to leave odd 1s
                                return f"{i},{take + 1}"
                        else:
                            # XOR = 0 with some pile > 1: P-position
                            return f"{i},{take}"
    
    # P-position or all piles <= 1: make any legal move
    for i in range(n):
        if piles[i] > 0:
            return f"{i},1"
    
    # Game already over (shouldn't reach here in normal play)
    return "0,1"
