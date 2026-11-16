
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If Nim-sum is 0, we're in a losing position
    # Just take 1 from the first non-empty pile
    if nim_sum == 0:
        for i in range(len(piles)):
            if piles[i] > 0:
                return f"{i},1"
    
    # If Nim-sum is non-zero, find a winning move
    # We want to make a move that results in Nim-sum of 0
    for i in range(len(piles)):
        if piles[i] > 0:
            # What should this pile's size be to make Nim-sum = 0?
            target_size = nim_sum ^ piles[i]
            
            # If target size is less than current pile size, we can make this move
            if target_size < piles[i]:
                take = piles[i] - target_size
                return f"{i},{take}"
    
    # Fallback (should never reach here with legal positions)
    # Take 1 from the first non-empty pile
    for i in range(len(piles)):
        if piles[i] > 0:
            return f"{i},1"
