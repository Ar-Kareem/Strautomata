
def policy(piles: list[int]) -> str:
    # Calculate nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim-sum is 0, we are in a losing position
    # Play randomly (but legally) to avoid guaranteed loss
    if nim_sum == 0:
        # Just take 1 from the first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # If nim-sum is not 0, find a move to make it 0
    for i in range(4):
        # Target size for this pile to make nim-sum 0
        target = nim_sum ^ piles[i]
        # If we can reduce this pile to 'target' size
        if target < piles[i]:
            # Take enough stones to reach target size
            take = piles[i] - target
            return f"{i},{take}"
    
    # Fallback (should never reach here in valid game state)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
