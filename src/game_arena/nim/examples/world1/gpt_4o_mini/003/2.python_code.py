
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim_sum is 0, we can only make a non-advantageous move.
    for i in range(4):
        if piles[i] > 0:
            # Take one from any pile (this is a legal move and keeps it simple)
            return f"{i},1"
    
    # If nim_sum is non-zero, we need to find a pile to take from to make nim_sum zero
    for i in range(4):
        target_size = piles[i] ^ nim_sum
        if target_size < piles[i]:
            # This means we can adjust pile[i] down to target_size
            take = piles[i] - target_size
            return f"{i},{take}"
    
    # Fallback (should not occur)
    return "0,1"
