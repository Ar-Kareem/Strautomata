
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all piles are <= 1
    all_small = all(p <= 1 for p in piles)
    
    if all_small:
        # Misère endgame: we want to leave an odd number of 1-piles
        # (so opponent faces odd piles and is forced to take the last)
        non_empty = sum(1 for p in piles if p > 0)
        if non_empty % 2 == 0:
            # Even non-empty piles, take one to make it odd for opponent
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Odd non-empty piles - we're in trouble, just move
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    
    # Normal play phase: at least one pile >= 2
    if nim_sum == 0:
        # Losing position - make a move, prefer taking from largest pile
        # Try to make a reasonable move
        best_pile = -1
        best_size = 0
        for i in range(4):
            if piles[i] > best_size:
                best_size = piles[i]
                best_pile = i
        return f"{best_pile},1"
    
    # Nim-sum != 0: we can win with perfect play
    for i in range(4):
        if piles[i] == 0:
            continue
        target = piles[i] ^ nim_sum
        if target < piles[i]:
            take = piles[i] - target
            # Check resulting position
            new_piles = piles[:]
            new_piles[i] = target
            
            # Check if resulting position has all piles <= 1
            all_new_small = all(p <= 1 for p in new_piles)
            
            if all_new_small:
                # Misère twist: leave odd number of 1-piles for opponent
                ones = sum(1 for p in new_piles if p == 1)
                if ones % 2 == 1:
                    # Good - opponent faces odd 1-piles and loses
                    return f"{i},{take}"
                else:
                    # This would leave even 1-piles - bad for misère
                    # Try adjusting: take one more (reduce target by 1) or one less
                    # Actually, take all from this pile instead if target > 0
                    # We need to leave odd number of 1s
                    # Try taking everything (target=0) vs leaving 1 (target=1)
                    for t in [0, 1]:
                        if t < piles[i]:
                            test_piles = piles[:]
                            test_piles[i] = t
                            if all(p <= 1 for p in test_piles):
                                ones_t = sum(1 for p in test_piles if p == 1)
                                if ones_t % 2 == 1:
                                    return f"{i},{piles[i] - t}"
                    # Fallback
                    return f"{i},{take}"
            else:
                return f"{i},{take}"
    
    # Fallback: should not reach here
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
