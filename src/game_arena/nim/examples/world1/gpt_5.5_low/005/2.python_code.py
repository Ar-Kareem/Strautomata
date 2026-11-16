
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Defensive normalization: assume valid input, but avoid surprises.
    piles = list(piles)

    # Find legal piles.
    nonzero = [i for i, p in enumerate(piles) if p > 0]

    # Terminal state should not be queried because no legal move exists.
    # Still return a syntactically valid string as a last-resort fallback.
    if not nonzero:
        return "0,0"

    big = [i for i, p in enumerate(piles) if p > 1]
    ones_count = sum(1 for p in piles if p == 1)

    # Misere endgame: all remaining piles are size 1.
    # Any move is forced; take one from a non-empty pile.
    if not big:
        return f"{nonzero[0]},1"

    # If exactly one pile has more than 1 object, move to an odd number
    # of single-object piles for the opponent.
    if len(big) == 1:
        i = big[0]
        current = piles[i]

        # Choose remaining amount r in {0, 1} so that ones_count + r is odd.
        # If ones_count is odd, reduce big pile to 0.
        # If ones_count is even, reduce big pile to 1.
        target_remaining = 0 if ones_count % 2 == 1 else 1
        take = current - target_remaining

        if take >= 1:
            return f"{i},{take}"

        # Safety fallback, though this should not occur for current > 1.
        return f"{i},1"

    # General case: more than one pile has size > 1.
    # Use normal Nim strategy: move to xor 0 when possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Losing position fallback: make a legal move.
    # Prefer taking one from the largest pile to preserve flexibility.
    max_i = max(nonzero, key=lambda idx: piles[idx])
    return f"{max_i},1"
