
def policy(piles: list[int]) -> str:
    # Count piles of size > 1 and piles of size == 1
    gt1_indices = [i for i, p in enumerate(piles) if p > 1]
    eq1_indices = [i for i, p in enumerate(piles) if p == 1]
    
    # Case 1: Exactly one pile of size > 1
    if len(gt1_indices) == 1:
        target_pile = gt1_indices[0]
        size = piles[target_pile]
        num_ones = len(eq1_indices)
        
        # We want to leave an ODD number of 1s
        if num_ones % 2 == 0:
            # Leave 1 in the target pile (num_ones + 1 is odd)
            take = size - 1
        else:
            # Clear the target pile completely (num_ones is odd)
            take = size
        return f"{target_pile},{take}"
        
    # Case 2: Zero piles of size > 1 (all non-empty piles are of size 1)
    if len(gt1_indices) == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Case 3: More than one pile of size > 1 (play standard Nim)
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target_size = p ^ xor_sum
            if target_size < p:
                take = p - target_size
                return f"{i},{take}"

    # If xor_sum is 0 (losing position), make a valid fallback move (take 1 from the largest pile)
    largest_pile = max(range(len(piles)), key=lambda i: piles[i])
    return f"{largest_pile},1"
