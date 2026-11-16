
def policy(piles: list[int]) -> str:
    # Calculate nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Check if we're in endgame (all piles <= 1)
    in_endgame = all(pile <= 1 for pile in piles)
    
    if in_endgame:
        # Count non-empty piles
        non_empty_count = sum(1 for pile in piles if pile > 0)
        # In misère game, we want to leave opponent with odd number of piles
        # If we have odd number of piles, take from any pile to make it even
        # If we have even number of piles, take from any pile to make it odd (but prefer to not lose immediately)
        for i in range(4):
            if piles[i] > 0:
                # Taking 1 from this pile
                remaining_piles = non_empty_count - 1
                # If remaining is odd, opponent loses
                return f"{i},1"
    else:
        # Not in endgame, play normal nim strategy but be careful
        # Try to make nim-sum = 0
        for i in range(4):
            if piles[i] > 0:
                # What should this pile be to make nim-sum = 0?
                target = nim_sum ^ piles[i]
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
        
        # If we can't make nim-sum 0, just take 1 from first available pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Fallback (should never reach here with legal game states)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
