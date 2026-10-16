
def policy(piles: list[int]) -> str:
    # Calculate the XOR sum of all piles
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # If the XOR sum is 0, we must make a move that doesn't preserve this
    # Or if we're in a losing position, try to leave opponent with losing state
    if xor_sum == 0:
        # Any move is acceptable
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
    
    # Try to make a move that results in a state with XOR sum 0
    n = len(piles)
    for i in range(n):
        if piles[i] > 0:
            # Find the target pile size that will result in xor_sum = 0
            target = piles[i] ^ xor_sum
            if target < piles[i]:
                # We can reduce pile i to target
                take = piles[i] - target
                return f"{i},{take}"
    
    # This should not happen in normal circumstances but as last resort:
    # make any legal move
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
