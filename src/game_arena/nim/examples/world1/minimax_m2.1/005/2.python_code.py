
def policy(piles):
    # Check if all non-zero piles are size 1
    non_zero = [p for p in piles if p > 0]
    if all(p == 1 for p in non_zero):
        n = len(non_zero)
        # Even non-empty piles: winning position, take one pile to leave odd
        if n % 2 == 0:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        # Odd non-empty piles: losing position, take one pile
        else:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    
    # There is at least one pile > 1
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Winning branch: nim_sum != 0
    if nim_sum != 0:
        # Try to leave nim_sum=0 without creating even non-empty all-ones state
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    new_state = piles[:]
                    new_state[i] = target
                    # Check if new_state is all ones
                    if all(x <= 1 for x in new_state):
                        non_empty = sum(1 for x in new_state if x > 0)
                        if non_empty % 2 == 0:
                            continue  # Skip: would leave winning position for opponent
                    take = piles[i] - target
                    return f"{i},{take}"
        
        # Try to leave odd non-empty all-ones state
        for i in range(4):
            if piles[i] > 0:
                # Reduce to 0
                new_state = piles[:]
                new_state[i] = 0
                if all(x <= 1 for x in new_state):
                    non_empty = sum(1 for x in new_state if x > 0)
                    if non_empty % 2 == 1:
                        take = piles[i]
                        return f"{i},{take}"
                # Reduce to 1
                if piles[i] > 1:
                    new_state = piles[:]
                    new_state[i] = 1
                    if all(x <= 1 for x in new_state):
                        non_empty = sum(1 for x in new_state if x > 0)
                        if non_empty % 2 == 1:
                            take = piles[i] - 1
                            return f"{i},{take}"
        
        # Last resort: leave nim_sum=0 (any move)
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
        
        # Fallback: any legal move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Losing branch: nim_sum == 0
    else:
        # Try to leave odd non-empty all-ones state
        for i in range(4):
            if piles[i] > 0:
                # Reduce to 0
                new_state = piles[:]
                new_state[i] = 0
                if all(x <= 1 for x in new_state):
                    non_empty = sum(1 for x in new_state if x > 0)
                    if non_empty % 2 == 1:
                        take = piles[i]
                        return f"{i},{take}"
                # Reduce to 1
                if piles[i] > 1:
                    new_state = piles[:]
                    new_state[i] = 1
                    if all(x <= 1 for x in new_state):
                        non_empty = sum(1 for x in new_state if x > 0)
                        if non_empty % 2 == 1:
                            take = piles[i] - 1
                            return f"{i},{take}"
        
        # Fallback: any legal move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
