
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Last player to take an object loses.
    - Return format: 'pile,take'
    """

    legal_indices = [i for i, p in enumerate(piles) if p > 0]

    # Terminal positions should not be passed to the policy.
    # No legal move exists here, but return a formatted fallback.
    if not legal_indices:
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all remaining piles are size 1.
    # Odd number of ones is losing, even is winning.
    # In either case, the only type of legal move is taking one pile.
    if not big_indices:
        return f"{legal_indices[0]},1"

    # Case 2: exactly one pile has more than one object.
    # Move to an odd number of size-1 piles for the opponent.
    if len(big_indices) == 1:
        i = big_indices[0]
        h = piles[i]

        if ones % 2 == 0:
            # Leave this pile as a single object.
            take = h - 1
        else:
            # Remove this pile entirely.
            take = h

        return f"{i},{take}"

    # Case 3: at least two piles are larger than one.
    # Play normal Nim: move to xor zero whenever possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, h in enumerate(piles):
            target = h ^ xor_sum
            if target < h:
                take = h - target
                return f"{i},{take}"

    # Losing position under perfect play.
    # Return any legal move; removing one from the largest pile is safe.
    i = max(legal_indices, key=lambda idx: piles[idx])
    return f"{i},1"
