
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Defensive fallback: find any legal move.
    def legal_fallback() -> str:
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
        # No legal move exists in a terminal state; policy should not be called then.
        return "0,0"

    if not piles or len(piles) != 4:
        return legal_fallback()

    nonzero = [(i, x) for i, x in enumerate(piles) if x > 0]
    if not nonzero:
        return "0,0"

    big = [(i, x) for i, x in enumerate(piles) if x > 1]
    ones_count = sum(1 for x in piles if x == 1)

    # Case 1: all remaining piles are size 1.
    # Forced to take exactly one.
    if len(big) == 0:
        for i, x in enumerate(piles):
            if x == 1:
                return f"{i},1"

    # Case 2: exactly one pile larger than 1.
    # Leave the opponent an odd number of single-object piles.
    if len(big) == 1:
        i, x = big[0]

        # Choose whether to leave this big pile as 0 or 1.
        # We want ones_count + remaining_to_leave to be odd.
        if ones_count % 2 == 0:
            leave = 1
        else:
            leave = 0

        take = x - leave
        if take >= 1:
            return f"{i},{take}"
        return legal_fallback()

    # Case 3: normal Nim strategy applies.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(piles):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # Losing position under perfect play; return any legal move.
    # Prefer removing 1 from a largest pile to avoid accidental illegal choices.
    best_i = -1
    best_x = -1
    for i, x in enumerate(piles):
        if x > best_x:
            best_i = i
            best_x = x

    if best_x > 0:
        return f"{best_i},1"

    return legal_fallback()
