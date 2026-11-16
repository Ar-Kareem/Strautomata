
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Defensive fallback: find any legal move.
    def legal_fallback() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # This should never be called in a valid non-terminal game.
        return "0,0"

    # Count useful pile types.
    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    nonzero_indices = [i for i, p in enumerate(piles) if p > 0]

    if not nonzero_indices:
        return "0,0"

    # Case 1: all piles are size 0 or 1.
    # In misere Nim, an odd number of 1-piles is losing.
    # If even, take one and leave an odd number.
    if not big_indices:
        return f"{nonzero_indices[0]},1"

    # Case 2: exactly one pile larger than 1.
    # Reduce it to 0 or 1 so that the opponent faces an odd number of 1-piles.
    if len(big_indices) == 1:
        i = big_indices[0]
        pile_size = piles[i]

        # We want ones + remaining_value to be odd.
        # remaining_value must be either 0 or 1.
        remaining_value = 1 if ones % 2 == 0 else 0
        take = pile_size - remaining_value

        if take >= 1:
            return f"{i},{take}"
        return legal_fallback()

    # Case 3: at least two piles larger than 1.
    # Use the normal Nim xor move unless already in a losing xor-zero position.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum == 0:
        # Losing under perfect play; still return a legal move.
        # Prefer taking one from a largest pile to avoid immediate blunders.
        i = max(nonzero_indices, key=lambda idx: piles[idx])
        return f"{i},1"

    # Find a pile that can be reduced to make xor zero.
    for i, p in enumerate(piles):
        target = p ^ xor_sum
        if target < p:
            take = p - target
            if take >= 1:
                return f"{i},{take}"

    return legal_fallback()
