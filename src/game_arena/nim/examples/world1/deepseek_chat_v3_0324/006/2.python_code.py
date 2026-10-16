
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If Nim-sum is non-zero, find a winning move
    if nim_sum != 0:
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # If Nim-sum is zero (losing position), take from largest pile to minimize options
    max_pile = 0
    max_size = 0
    for i in range(4):
        if piles[i] > max_size:
            max_size = piles[i]
            max_pile = i
    
    if max_size == 0:  # Shouldn't happen since it's our turn
        return "0,1"
    
    # Take 1 from the largest pile (or all if only 1 remains)
    take = 1 if max_size > 1 else 1
    return f"{max_pile},{take}"
