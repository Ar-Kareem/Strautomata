
def policy(piles: list[int]) -> str:
    # Count piles with more than 1 object
    big_piles = [i for i in range(4) if piles[i] > 1]
    num_big = len(big_piles)
    
    # Case 1: no piles with more than 1 (all are 0 or 1)
    if num_big == 0:
        # Find the first pile that has 1 and take it
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
        # If none, but that should not happen as game would be over
        # But in case, take from any non-zero (shouldn't occur)
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
                
    # Case 2: exactly one pile has more than 1
    elif num_big == 1:
        big_index = big_piles[0]
        # Count number of piles with exactly 1
        ones = sum(1 for x in piles if x == 1)
        if ones % 2 == 1:
            # Reduce the big pile to 0
            take = piles[big_index]
            return f"{big_index},{take}"
        else:
            # Reduce the big pile to 1
            take = piles[big_index] - 1
            return f"{big_index},{take}"
            
    # Case 3: two or more piles have more than 1 -> normal nim
    else:
        # Compute nim-sum
        nim = 0
        for x in piles:
            nim ^= x
            
        if nim == 0:
            # Losing position in normal play; make a minimal move
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Try to find a move that makes nim-sum 0
            for i in range(4):
                if piles[i] > 0:
                    target = nim ^ piles[i]
                    if target < piles[i]:
                        take = piles[i] - target
                        return f"{i},{take}"
            # If no move found (should not happen), make a fallback move
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
