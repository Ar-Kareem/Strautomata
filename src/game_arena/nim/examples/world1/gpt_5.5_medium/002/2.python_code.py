
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Move format: 'pile,take'
    Rule: player who takes the last object loses.
    """

    # Find non-empty piles.
    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # Terminal states should not be queried, since no legal move exists.
    # Return a harmless fallback string if it ever happens.
    if not nonzero:
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    big = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all remaining piles are size 1.
    # With k singletons, the player to move wins iff k is even.
    # The only legal move is to remove one singleton.
    if not big:
        return f"{nonzero[0]},1"

    # Case 2: exactly one pile has size greater than 1.
    # Move so the opponent faces an odd number of singleton piles.
    if len(big) == 1:
        i = big[0]
        n = piles[i]

        if ones % 2 == 1:
            # Leave the existing odd number of singleton piles.
            take = n
        else:
            # Turn the big pile into one more singleton, making the count odd.
            take = n - 1

        return f"{i},{take}"

    # Case 3: at least two big piles.
    # In this region, misere Nim is played like normal Nim:
    # move to xor zero if possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                return f"{i},{take}"

    # Losing position under perfect play.
    # Still return a legal move. Removing 1 from a largest pile is safe.
    i = max(nonzero, key=lambda idx: piles[idx])
    return f"{i},1"
