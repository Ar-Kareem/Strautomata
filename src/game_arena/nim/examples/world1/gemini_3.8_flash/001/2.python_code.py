
def policy(piles: list[int]) -> str:
    # Count piles of size > 1 and size == 1
    piles_gt_1 = [i for i, p in enumerate(piles) if p > 1]
    piles_eq_1 = [i for i, p in enumerate(piles) if p == 1]

    # Case 1: Exactly one pile has size > 1
    if len(piles_gt_1) == 1:
        target_idx = piles_gt_1[0]
        num_ones = len(piles_eq_1)
        # We want to leave an ODD number of 1s after our move.
        # If the current number of 1s is odd, reduce this pile to 0.
        # If the current number of 1s is even, reduce this pile to 1.
        if num_ones % 2 == 1:
            take = piles[target_idx]
        else:
            take = piles[target_idx] - 1
        return f"{target_idx},{take}"

    # Case 2: All piles have size <= 1
    if len(piles_gt_1) == 0:
        if piles_eq_1:
            return f"{piles_eq_1[0]},1"
        # Fallback for empty state (should not occur)
        return "0,1"

    # Case 3: Two or more piles have size > 1 (standard Nim-sum play)
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target_size = p ^ xor_sum
            if target_size < p:
                take = p - target_size
                return f"{i},{take}"

    # If xor_sum is 0, we are in a losing position; take 1 from the largest pile
    max_idx = max(range(len(piles)), key=lambda i: piles[i])
    return f"{max_idx},1"
