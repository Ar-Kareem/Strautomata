
def policy(piles: list[int]) -> str:
    # Calculate nim-sum (XOR) of all piles
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # If nim-sum is 0, we're in a losing position
    # Find any move that makes nim-sum non-zero
    if nim_sum == 0:
        # For a losing position, try to make a move that leaves 
        # the opponent in a winning position
        # We want to change one pile so that the new nim-sum is non-zero
        for i in range(4):
            if piles[i] > 0:
                # Try taking 1 from any non-empty pile
                return f"{i},1"
    
    # If nim-sum is non-zero, make a move that makes nim-sum = 0
    # Find a pile that when reduced makes the overall nim-sum 0
    for i in range(4):
        if piles[i] > 0:
            # Target is the XOR of current nim_sum and pile size
            target_size = nim_sum ^ piles[i]
            if target_size < piles[i]:
                # We can take piles[i] - target_size objects from pile i
                take = piles[i] - target_size
                return f"{i},{take}"
    
    # Fallback - if for some reason the above doesn't work
    # Just take 1 from the first non-empty pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
