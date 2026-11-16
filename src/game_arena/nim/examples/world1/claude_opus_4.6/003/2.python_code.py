
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all piles are <= 1 (endgame)
    max_pile = max(piles)
    
    if max_pile <= 1:
        # Endgame: leave an odd number of 1-piles (opponent takes last)
        ones = sum(1 for p in piles if p == 1)
        if ones % 2 == 0:
            # We need to take from a pile with 1 to make it odd
            # But if ones is 0, we've already lost (no moves). Shouldn't happen since we must move.
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # Odd number of 1s, we must take one (making it even — bad for us, but forced)
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
    
    # Normal play phase (at least one pile > 1)
    if nim_sum == 0:
        # Losing position — make any legal move, preferably something reasonable
        # Try to take 1 from the largest pile
        largest_idx = max(range(4), key=lambda i: piles[i])
        return f"{largest_idx},1"
    
    # Winning position: find a move that makes nim_sum = 0
    # For misère, when the resulting position has all piles <= 1, 
    # we want an odd number of 1-piles remaining.
    
    for i in range(4):
        if piles[i] == 0:
            continue
        # Target for this pile to zero out the nim_sum
        target = piles[i] ^ nim_sum
        if target < piles[i]:
            take = piles[i] - target
            # Check resulting position
            new_piles = piles[:]
            new_piles[i] = target
            new_max = max(new_piles)
            
            if new_max <= 1:
                # Endgame check: need odd number of 1-piles
                ones = sum(1 for p in new_piles if p == 1)
                if ones % 2 == 1:
                    # Good — opponent faces odd 1-piles, will take last
                    return f"{i},{take}"
                else:
                    # Bad — try adjusting: instead of target, try target ± 1 if valid
                    # Actually, let's try other piles first
                    continue
            else:
                return f"{i},{take}"
    
    # If we got here, all nim_sum-zeroing moves lead to bad endgames
    # We need to adjust: leave an even number of 1-piles instead
    for i in range(4):
        if piles[i] == 0:
            continue
        target = piles[i] ^ nim_sum
        if target < piles[i]:
            take = piles[i] - target
            new_piles = piles[:]
            new_piles[i] = target
            # Adjust by ±1 if possible to fix parity
            # Try taking one more (target - 1) if target >= 0
            if target >= 1:
                adj_piles = piles[:]
                adj_piles[i] = target - 1
                if max(adj_piles) <= 1 and sum(1 for p in adj_piles if p == 1) % 2 == 1:
                    return f"{i},{take + 1}"
            if target + 1 < piles[i]:
                adj_piles = piles[:]
                adj_piles[i] = target + 1
                if max(adj_piles) <= 1 and sum(1 for p in adj_piles if p == 1) % 2 == 1:
                    return f"{i},{take - 1}"
            return f"{i},{take}"
    
    # Fallback: any legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
