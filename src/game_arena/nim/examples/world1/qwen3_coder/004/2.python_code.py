
def policy(piles: list[int]) -> str:
    # Calculate nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim-sum is 0, we're in a losing position
    # Make a safe move (take 1 from the largest pile)
    if nim_sum == 0:
        # Find the largest pile
        max_pile_index = 0
        max_pile_size = piles[0]
        for i in range(1, 4):
            if piles[i] > max_pile_size:
                max_pile_size = piles[i]
                max_pile_index = i
        
        # If the largest pile only has 1 object, take it
        # Otherwise take 1 object from it
        return f"{max_pile_index},1"
    
    # If nim-sum is not 0, find a winning move
    # We want to make a move that results in nim-sum of 0
    for i in range(4):
        # Calculate what the pile size should be after our move
        target_size = piles[i] ^ nim_sum
        
        # If this is a valid move (target size is less than current size)
        if target_size < piles[i]:
            # Return the move
            take = piles[i] - target_size
            return f"{i},{take}"
    
    # Fallback (should never reach here with valid input)
    # Just take 1 from the first non-empty pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
