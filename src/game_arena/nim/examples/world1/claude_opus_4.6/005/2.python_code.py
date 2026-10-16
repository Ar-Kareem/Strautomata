
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all piles are <= 1
    max_pile = max(piles)
    
    if max_pile <= 1:
        # Endgame: all piles are 0 or 1
        # We want to leave an odd number of 1s for the opponent (so opponent takes last)
        # Count piles with 1
        ones = sum(1 for p in piles if p == 1)
        # If ones is odd, we're losing (we must take one, leaving even for opponent, opponent leaves odd back...)
        # Actually if ones is odd, we take 1 from a pile with 1, leaving even ones for opponent -> opponent loses
        # Wait: if ones is odd, current player takes one -> ones becomes even -> opponent faces even ones
        # Even ones: opponent takes one -> odd ones for us... eventually last person to take loses
        # If ones is odd: we take, leaving even. Opponent takes, leaving odd... person facing 1 pile takes it and loses.
        # So if ones is odd, current player is in losing position (they must take, leaving even for opponent, who wins)
        # Just pick any pile with 1
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
    
    # Some pile > 1: standard misère Nim strategy
    if nim_sum == 0:
        # Losing position - make any legal move
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Nim-sum != 0: we can win
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            # Check if after this move, all piles <= 1
            new_piles = piles[:]
            new_piles[i] = target
            if all(np <= 1 for np in new_piles):
                # Count remaining piles with objects (all are 0 or 1)
                ones_left = sum(1 for np in new_piles if np == 1)
                if ones_left % 2 == 1:
                    # Odd number of 1-piles left for opponent -> opponent loses. Good!
                    return f"{i},{take}"
                else:
                    # Even number -> bad. Adjust: take one more or one less if possible
                    # If target > 0, take one more (leave target-1)
                    if target >= 1:
                        return f"{i},{take + 1}"
                    else:
                        # target is 0, try taking one less (leave 1)
                        if take > 1:
                            return f"{i},{take - 1}"
                        # Otherwise this specific pile doesn't work, try others
                        continue
            else:
                return f"{i},{take}"
    
    # Fallback (shouldn't reach here with nim_sum != 0, but safety)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
