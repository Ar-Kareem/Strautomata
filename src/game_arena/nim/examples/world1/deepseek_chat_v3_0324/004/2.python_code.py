
def policy(piles: list[int]) -> str:
    # Calculate Nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # Check if all piles are size 1 (special case)
    all_ones = all(pile <= 1 for pile in piles)
    if all_ones:
        # Must take last object (losing move)
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"

    # Find optimal move to make Nim-sum zero
    for i in range(4):
        if piles[i] == 0:
            continue
        target_size = nim_sum ^ piles[i]
        if target_size < piles[i]:
            take = piles[i] - target_size
            # Check if this would leave exactly one pile >1 (which is bad in misère)
            temp_piles = piles.copy()
            temp_piles[i] -= take
            piles_gt_1 = sum(1 for p in temp_piles if p > 1)
            if piles_gt_1 != 1 or all(p <= 1 for p in temp_piles):
                return f"{i},{take}"

    # If no optimal move found (shouldn't happen in winning position), take from largest pile
    max_pile = max(piles)
    pile_index = piles.index(max_pile)
    return f"{pile_index},1"
