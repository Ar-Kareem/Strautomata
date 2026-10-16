
def policy(piles: list[int]) -> str:
    # Check if all non-zero piles have size 1
    non_zero = [x for x in piles if x > 0]
    if len(non_zero) > 0 and all(x == 1 for x in non_zero):
        # All non-zero piles are size 1, take one from the first
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    # Compute nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim_sum is non-zero, find a winning move
    for idx in range(4):
        x = piles[idx]
        if x == 0:
            continue
        desired = nim_sum ^ x
        if desired < x:
            take = x - desired
            return f"{idx},{take}"
    
    # If nim_sum is zero, make any legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    # This line is theoretically unreachable due to game rules
    return ""
