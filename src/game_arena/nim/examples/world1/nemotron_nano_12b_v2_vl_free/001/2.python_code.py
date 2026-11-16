
def policy(piles: list[int]) -> str:
    # Check if all piles are 1
    all_ones = all(p == 1 for p in piles)
    if all_ones:
        # Take one from the first non-zero pile
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    else:
        # Compute the nim-sum
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        # Find a move to make nim_sum zero
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
        # Fallback if no move found (nim_sum is zero)
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
