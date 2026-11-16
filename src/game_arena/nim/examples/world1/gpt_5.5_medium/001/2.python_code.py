
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Move format: 'pile,take'
    The player taking the last object loses.
    """

    # Collect legal pile indices.
    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # Terminal state should not be queried because no legal move exists.
    # Return a harmless formatted fallback if it ever happens.
    if not nonzero:
        return "0,0"

    # Count piles by size class.
    ones = [i for i, p in enumerate(piles) if p == 1]
    bigs = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all nonzero piles are size 1.
    # With k ones, the position is winning iff k is even.
    # The only legal move is to remove one object from a size-1 pile.
    if not bigs:
        return f"{ones[0]},1"

    # Case 2: exactly one pile has more than 1 object.
    # Move so that the opponent is left with an odd number of 1-piles.
    if len(bigs) == 1:
        i = bigs[0]
        h = piles[i]
        one_count = len(ones)

        if one_count % 2 == 0:
            # Leave this pile as a single object, making odd total ones.
            take = h - 1
        else:
            # Remove this pile entirely, preserving odd total ones.
            take = h

        return f"{i},{take}"

    # Case 3: at least two piles are larger than 1.
    # Use normal Nim xor strategy.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if take >= 1:
                    return f"{i},{take}"

    # Losing position under perfect play: return any legal move.
    # Prefer removing one from a largest pile to keep the game nontrivial.
    best_i = max(nonzero, key=lambda idx: piles[idx])
    return f"{best_i},1"
