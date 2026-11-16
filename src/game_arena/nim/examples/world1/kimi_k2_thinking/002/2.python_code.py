
def policy(piles: list[int]) -> str:
    xor = 0
    ones = 0
    large_indices = []
    
    for i, p in enumerate(piles):
        xor ^= p
        if p == 1:
            ones += 1
        if p > 1:
            large_indices.append(i)
    
    # Case: all piles are size 0 or 1
    if not large_indices:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Case: at least one pile > 1 and we have a winning position (xor != 0)
    if xor != 0:
        # Special case: exactly one large pile
        if len(large_indices) == 1:
            i = large_indices[0]
            p = piles[i]
            # Want to leave odd number of 1s for opponent (losing position)
            if ones % 2 == 1:
                # Leave ones ones by reducing large pile to 0
                return f"{i},{p}"
            else:
                # Leave ones+1 ones by reducing large pile to 1
                return f"{i},{p - 1}"
        
        # General case: multiple large piles - standard Nim move
        for i, p in enumerate(piles):
            if p > 0:
                target = p ^ xor
                if target < p:
                    return f"{i},{p - target}"
    
    # Default: losing position or no good winning move found
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
