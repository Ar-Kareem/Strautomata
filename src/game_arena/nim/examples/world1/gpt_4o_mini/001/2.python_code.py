
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If Nim-sum is zero, we cannot win directly. We need to make a legal move.
    if nim_sum == 0:
        # Take from the smallest pile (but valid) to minimize our impact
        for i, pile in enumerate(piles):
            if pile > 0:
                return f'{i},1'
    
    # Find a move that makes the Nim-sum zero
    for i in range(len(piles)):
        if piles[i] > 0:
            new_pile_size = piles[i] ^ nim_sum
            # If this new size is less than current size, make the move
            if new_pile_size < piles[i]:
                take = piles[i] - new_pile_size
                return f'{i},{take}'
    
    # Fallback, should never reach here because valid moves always exist
    return '0,1'
