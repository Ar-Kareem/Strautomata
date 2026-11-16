
def policy(piles: list[int]) -> str:
    # Check if all piles are 1
    if all(p == 1 for p in piles):
        # All piles are 1: take one pile if even count, else take one pile (losing position)
        return '0,1'
    
    # Calculate nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim-sum is non-zero, find winning move
    if nim_sum != 0:
        for i, p in enumerate(piles):
            if p == 0:
                continue
            target = nim_sum ^ p
            if target < p:
                take = p - target
                return f"{i},{take}"
    
    # If nim-sum is zero, make any legal move (losing position)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
