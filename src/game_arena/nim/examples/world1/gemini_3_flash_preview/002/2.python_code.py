
def policy(piles: list[int]) -> str:
    # Calculate the XOR sum (Nim-sum) of the piles
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Count how many piles have more than 1 object
    piles_greater_than_1 = sum(1 for p in piles if p > 1)

    # Misere Play adjustment: 
    # If only one pile has more than 1 object, we want to leave an ODD number of 1s.
    if piles_greater_than_1 == 1:
        # Find the index of the pile with more than 1
        idx = next(i for i, p in enumerate(piles) if p > 1)
        # Count how many other piles have exactly 1
        count_ones = sum(1 for i, p in enumerate(piles) if i != idx and p == 1)
        
        # If count_ones is even, we leave 1 in this pile (total ones will be odd)
        # If count_ones is odd, we leave 0 in this pile (total ones will be odd)
        take = piles[idx] - 1 if count_ones % 2 == 0 else piles[idx]
        return f"{idx},{take}"

    # Standard Nim strategy: make the Nim-sum zero
    if nim_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                take = p - target
                return f"{i},{take}"

    # If already in a losing position (nim_sum == 0), take 1 from the first available pile
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    # Default fallback (should not reach here if state is legal)
    return "0,1"
