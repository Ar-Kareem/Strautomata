
def policy(piles: list[int]) -> str:
    # Count piles with size > 1
    c = sum(1 for p in piles if p > 1)
    # Count piles with size exactly 1
    k = sum(1 for p in piles if p == 1)
    
    # Case 1: All piles are 0 or 1 (endgame)
    if c == 0:
        # Find first non-empty pile
        for i, p in enumerate(piles):
            if p > 0:
                # Always take 1; if k is even we win, if k is odd we lose anyway
                return f"{i},1"
        # Should not reach here (no legal move), but return default
        return "0,0"
    
    # Case 2: Exactly one pile > 1
    if c == 1:
        # Find the large pile
        large_idx = -1
        large_val = 0
        for i, p in enumerate(piles):
            if p > 1:
                large_idx = i
                large_val = p
                break
        
        if k % 2 == 1:
            # k is odd, take entire pile to leave k piles (odd)
            return f"{large_idx},{large_val}"
        else:
            # k is even, leave 1 in large pile to make k+1 piles (odd)
            return f"{large_idx},{large_val - 1}"
    
    # Case 3: Two or more piles > 1 (standard Nim with misère adjustment not needed)
    # Compute nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum == 0:
        # Losing position, make any legal move
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"
    else:
        # Winning position: find pile where pile XOR nim_sum < pile
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                take = p - target
                return f"{i},{take}"
        # Fallback (should not happen)
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"
