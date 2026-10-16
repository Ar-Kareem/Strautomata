
def policy(piles: list[int]) -> str:
    # Calculate the XOR (Nim-sum) of all piles
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # If we're in a losing position (XOR = 0), make any legal move
    if xor_sum == 0:
        # Find any non-empty pile and take one object
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # If we're in a winning position, find a move to make XOR = 0
    # For each pile, calculate what its size should be to make XOR = 0
    for i in range(4):
        # Calculate target size for this pile to make XOR = 0
        target_size = xor_sum ^ piles[i]
        # If target size is less than current size, we can make this move
        if target_size < piles[i]:
            # Take enough objects to reduce pile to target_size
            take = piles[i] - target_size
            return f"{i},{take}"
    
    # Fallback - should not reach here in valid Nim positions
    # Find any legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
