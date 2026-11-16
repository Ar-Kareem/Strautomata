
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Check if we can move to a state with only piles of size 1
    # Count how many piles have more than 1 object
    piles_greater_than_1 = sum(1 for p in piles if p > 1)

    if piles_greater_than_1 <= 1:
        # Misere play endgame: leave an odd number of piles of size 1
        # Find the'big' pile index (if any) or any non-empty pile
        target_pile = -1
        for i, p in enumerate(piles):
            if p > 1:
                target_pile = i
                break
        
        if target_pile != -1:
            # Count how many other piles have exactly 1
            other_ones = sum(1 for i, p in enumerate(piles) if i != target_pile and p == 1)
            # If other_ones is even, we want to leave 1 in this pile (total odd)
            # If other_ones is odd, we want to leave 0 in this pile (total odd)
            take = piles[target_pile] - (1 if other_ones % 2 == 0 else 0)
            return f"{target_pile},{take}"
        else:
            # All piles are 0 or 1. Just take 1 from any non-empty pile.
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"

    # Standard Nim-sum strategy
    if nim_sum != 0:
        for i, p in enumerate(piles):
            target_size = p ^ nim_sum
            if target_size < p:
                return f"{i},{p - target_size}"

    # If the position is losing (nim_sum 0), make the smallest possible legal move
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
            
    return "0,0" # Should never be reached in legal play
