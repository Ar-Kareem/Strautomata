
def policy(piles: list[int]) -> str:
    # Count non-empty piles and piles with more than 1 stone
    non_empty_piles = sum(1 for p in piles if p > 0)
    large_piles = sum(1 for p in piles if p > 1)
    
    # If we're in endgame (all piles are 0 or 1)
    if large_piles == 0:
        # Count piles of size 1
        ones = sum(1 for p in piles if p == 1)
        # In misère, if all piles are size 1, we want to leave odd number for opponent
        # If we face odd number, we lose; if we face even number, we win
        for i in range(4):
            if piles[i] > 0:
                # Take from any pile of size 1
                return f"{i},1"
    
    # Calculate nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim-sum is 0, we're in a losing position (assuming optimal opponent)
    # Make any legal move - try to take just 1 from the largest pile
    if nim_sum == 0:
        # Find the largest pile
        max_size = max(piles)
        for i in range(4):
            if piles[i] == max_size:
                return f"{i},1"
    
    # If nim-sum is not 0, we're in a winning position
    # Find a move that makes nim-sum = 0
    for i in range(4):
        if piles[i] > 0:
            # What should this pile become to make nim-sum = 0?
            target_size = piles[i] ^ nim_sum
            if target_size < piles[i]:
                # We can make this move
                take = piles[i] - target_size
                return f"{i},{take}"
    
    # Fallback - should never reach here for legal positions
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
