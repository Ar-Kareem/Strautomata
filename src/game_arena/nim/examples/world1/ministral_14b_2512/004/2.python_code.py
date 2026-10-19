
def policy(piles: list[int]) -> str:
    # Compute the nim-sum (XOR of all piles)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If nim-sum is non-zero, play standard Nim (reduce nim-sum to zero)
    if nim_sum != 0:
        for i in range(4):
            if (piles[i] ^ nim_sum) < piles[i]:
                take = piles[i] - (piles[i] ^ nim_sum)
                return f"{i},{take}"

    # If nim-sum is zero, we are in a losing position if opponent plays optimally.
    # For 4 piles, the strategy is to leave all piles equal or reduce the largest pile to match the second-largest.
    # First, check if all piles are equal (losing position)
    if all(p == piles[0] for p in piles):
        # If all piles are equal and non-zero, take 1 from any pile (forcing opponent to break symmetry)
        return f"0,1"

    # Find the largest pile
    max_pile = max(piles)
    max_index = piles.index(max_pile)

    # If there are multiple piles with max_pile, choose the first one
    if piles.count(max_pile) > 1:
        max_index = piles.index(max_pile)

    # If the largest pile is not unique, reduce it to match the second-largest
    second_largest = sorted(piles, reverse=True)[1]
    if max_pile != second_largest:
        take = max_pile - second_largest
        return f"{max_index},{take}"

    # If all piles are equal except one, reduce the largest to match the others
    # This is a fallback (should not happen if nim-sum is zero and not all equal)
    for i in range(4):
        if piles[i] != piles[0]:
            take = piles[i] - piles[0]
            return f"{i},{take}"

    # Fallback: take 1 from any pile (should not reach here for valid inputs)
    return "0,1"
