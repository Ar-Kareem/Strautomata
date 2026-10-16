
def policy(piles: list[int]) -> str:
    # Check if all piles are size 1
    if all(p == 1 for p in piles):
        # Find a pile with 1 object to remove
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    # Calculate XOR of all piles
    xor_sum = 0
    for p in piles:
        xor_sum ^= p
    
    # If XOR is 0, we're in a losing position
    if xor_sum == 0:
        # Make any legal move - find first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Find a pile where we can make XOR 0
    for i in range(4):
        if piles[i] > 0:
            # Calculate what the pile should be after our move
            target = piles[i] ^ xor_sum
            if target < piles[i]:
                # We can reduce this pile to target
                take = piles[i] - target
                return f"{i},{take}"
    
    # This should never happen with valid input
    return "0,1"
