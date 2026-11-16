
def policy(piles: list[int]) -> str:
    # Count piles strictly greater than 1 and piles equal to 1
    greater_than_one = [i for i, p in enumerate(piles) if p > 1]
    ones = [i for i, p in enumerate(piles) if p == 1]
    
    # Endgame Case 1: Exactly one pile with size > 1
    if len(greater_than_one) == 1:
        target_pile = greater_than_one[0]
        count_ones = len(ones)
        # We want to leave an odd number of piles of size 1
        if count_ones % 2 == 0:
            # Leave 1 in the target pile
            take = piles[target_pile] - 1
        else:
            # Leave 0 in the target pile
            take = piles[target_pile]
        return f"{target_pile},{take}"

    # Endgame Case 2: All piles have size <= 1
    if len(greater_than_one) == 0:
        target_pile = ones[0] if ones else 0
        return f"{target_pile},1"

    # Normal Play: At least two piles with size > 1
    # Standard Nim strategy: make the nim-sum (XOR sum) equal to 0
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum != 0:
        for i, p in enumerate(piles):
            target_size = p ^ nim_sum
            if target_size < p:
                take = p - target_size
                return f"{i},{take}"

    # If already in a nim-sum 0 position, make any legal move (take 1 from the largest pile)
    largest_pile = max(range(len(piles)), key=lambda i: piles[i])
    return f"{largest_pile},1"
