
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim_sum is zero, no winning move, just make a legal move
    if nim_sum == 0:
        for i in range(4):
            if piles[i] > 0:  # make a move from a non-empty pile
                return f'{i},1'  # take 1 from the first non-empty pile found
    
    # If nim_sum is not zero, find a winning move
    for i in range(4):
        desired_pile_size = piles[i] ^ nim_sum  # This is the size we want
        if desired_pile_size < piles[i]:  # We can reduce this pile
            take = piles[i] - desired_pile_size  # Calculate how much to take
            return f'{i},{take}'
    
    # Default fallback in case no move is found
    return '0,1'  # Shouldn't hit this case if the logic is correct
