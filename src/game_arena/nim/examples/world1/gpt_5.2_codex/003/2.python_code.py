
def policy(piles: list[int]) -> str:
    # Find any legal move if needed
    nonzero = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return "0,0"  # no legal move; should not be called
    
    # Case 1: all piles are 0 or 1
    if all(p <= 1 for p in piles):
        idx = nonzero[0]
        return f"{idx},1"
    
    # Count heaps greater than 1
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    
    # Case 2: exactly one heap larger than 1 (special misère rule)
    if len(big_indices) == 1:
        big = big_indices[0]
        ones = sum(1 for p in piles if p == 1)
        if ones % 2 == 0:
            take = piles[big] - 1  # leave one to make odd count of ones
        else:
            take = piles[big]      # take all to leave odd count of ones
        if take < 1:
            take = 1
        return f"{big},{take}"
    
    # Case 3: normal Nim play
    xor_sum = 0
    for p in piles:
        xor_sum ^= p
    
    if xor_sum == 0:
        idx = nonzero[0]
        return f"{idx},1"
    
    for i, p in enumerate(piles):
        target = p ^ xor_sum
        if target < p:
            take = p - target
            if take >= 1:
                return f"{i},{take}"
    
    # Fallback
    idx = nonzero[0]
    return f"{idx},1"
