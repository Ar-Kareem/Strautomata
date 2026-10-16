
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all piles are <= 1
    all_small = all(p <= 1 for p in piles)
    
    if all_small:
        # Misère endgame: we want to leave an ODD number of piles with 1
        # (so opponent faces odd piles and eventually takes the last)
        # If current number of 1s is even, we're winning (take one to make it odd)
        # If odd, we're losing, just take from any pile
        non_empty = [(i, p) for i, p in enumerate(piles) if p > 0]
        if not non_empty:
            # No legal move (shouldn't happen since we must move)
            return "0,1"
        # Take from the first non-empty pile
        return f"{non_empty[0][0]},1"
    
    # At least one pile has size >= 2
    if nim_sum == 0:
        # Losing position - make any legal move (prefer taking 1 from largest pile)
        # Actually, just pick any legal move
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Nim-sum != 0: we can make a winning move
    # For each pile, check if we can reduce it to make nim_sum 0
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            # Check the resulting state
            new_piles = piles[:]
            new_piles[i] = target
            
            # Check if resulting state has all piles <= 1
            all_new_small = all(np <= 1 for np in new_piles)
            
            if all_new_small:
                # Misère twist: we want to leave an ODD number of 1-piles
                # so opponent is forced to take last
                ones_count = sum(1 for np in new_piles if np == 1)
                if ones_count % 2 == 1:
                    # Good, this is what we want for misère
                    return f"{i},{take}"
                else:
                    # This would leave even 1s - bad for misère
                    # Try adjusting: take one more (leave target-1) or one less
                    # If target > 0, we can take one more to leave target-1
                    if target >= 1:
                        # Leave target-1 instead
                        new_target = target - 1
                        new_take = p - new_target
                        new_piles2 = piles[:]
                        new_piles2[i] = new_target
                        if all(np <= 1 for np in new_piles2) and sum(1 for np in new_piles2 if np == 1) % 2 == 1:
                            return f"{i},{new_take}"
                    # If target == 0 and we could take one less
                    if take > 1:
                        new_target = target + 1
                        new_piles2 = piles[:]
                        new_piles2[i] = new_target
                        if all(np <= 1 for np in new_piles2) and sum(1 for np in new_piles2 if np == 1) % 2 == 1:
                            return f"{i},{take - 1}"
                    # Fallback: still make this move
                    continue
            else:
                return f"{i},{take}"
    
    # Fallback: shouldn't reach here if nim_sum != 0, but just in case
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    return "0,1"
