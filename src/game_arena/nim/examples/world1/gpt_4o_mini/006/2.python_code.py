
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    if nim_sum == 0:
        # If nim sum is zero, choose any non-empty pile
        for i in range(len(piles)):
            if piles[i] > 0:
                return f"{i},{1}"  # Take one object from the first non-empty pile
    else:
        # Otherwise, find a move that makes the nim sum zero
        for i in range(len(piles)):
            if piles[i] > 0:
                new_pile_size = piles[i] ^ nim_sum
                if new_pile_size < piles[i]:
                    return f"{i},{piles[i] - new_pile_size}"  # Make the move that leads to a winning position
    return '0,1'  # Fallback, should not reach here due to above logic
