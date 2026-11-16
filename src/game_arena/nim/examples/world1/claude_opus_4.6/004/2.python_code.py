
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all piles are <= 1
    all_small = all(p <= 1 for p in piles)
    
    if all_small:
        # Misère endgame: we want to leave an even number of 1s
        # (so opponent faces odd number and is forced to take last)
        ones = sum(1 for p in piles if p == 1)
        if ones % 2 == 1:
            # Leave even number: take from a pile with 1
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # We're in a losing position, just move
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
    
    # Normal play phase: at least one pile > 1
    if nim_sum == 0:
        # Losing position - make any legal move, prefer taking from largest pile
        # to complicate things for opponent
        best_pile = -1
        best_size = 0
        for i in range(4):
            if piles[i] > best_size:
                best_size = piles[i]
                best_pile = i
        return f"{best_pile},1"
    
    # Nim-sum != 0: we can win
    for i in range(4):
        target = piles[i] ^ nim_sum
        if target < piles[i]:
            take = piles[i] - target
            # Check if after this move, all piles <= 1
            new_piles = piles[:]
            new_piles[i] = target
            all_small_after = all(p <= 1 for p in new_piles)
            
            if all_small_after:
                # Misère twist: we want odd number of piles with 1
                # (so opponent faces odd 1s and takes the last)
                ones_after = sum(1 for p in new_piles if p == 1)
                if ones_after % 2 == 1:
                    # Good, this is what we want
                    return f"{i},{take}"
                else:
                    # Adjust: instead of target, try target-1 or different approach
                    # We need to leave odd number of 1-piles
                    # If target == 1, try target = 0; if target == 0, try target = 1
                    if target == 0 and piles[i] >= 1:
                        alt_take = piles[i]
                        alt_piles = piles[:]
                        alt_piles[i] = 0
                        if all(p <= 1 for p in alt_piles) and sum(1 for p in alt_piles if p == 1) % 2 == 1:
                            return f"{i},{alt_take}"
                    if target >= 1:
                        alt_take = piles[i]  # take all, leaving 0
                        alt_piles = piles[:]
                        alt_piles[i] = 0
                        if all(p <= 1 for p in alt_piles) and sum(1 for p in alt_piles if p == 1) % 2 == 1:
                            return f"{i},{alt_take}"
                    # If we can't fix it easily, still make the move
                    return f"{i},{take}"
            else:
                return f"{i},{take}"
    
    # Fallback (should not reach here)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
