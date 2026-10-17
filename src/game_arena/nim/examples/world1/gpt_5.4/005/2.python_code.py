
def policy(piles: list[int]) -> str:
    # Ensure we always return a legal move if any legal move exists.
    # Game assumptions say length is 4, but we write this robustly.
    n = len(piles)

    # Collect nonzero piles and classify sizes.
    nonzero_indices = [i for i, x in enumerate(piles) if x > 0]
    if not nonzero_indices:
        # No legal move exists in a finished state; return a harmless default.
        # Arena should not call policy on terminal states.
        return "0,0"

    ones = sum(1 for x in piles if x == 1)
    bigs = [(i, x) for i, x in enumerate(piles) if x > 1]
    nonzero = len(nonzero_indices)

    # Misère Nim special case: all nonzero piles are size 1.
    if ones == nonzero:
        # Leave an odd number of 1-heaps to the opponent.
        # If current count is even, remove one heap -> odd for opponent (winning).
        # If current count is odd, any move loses; remove one heap legally.
        i = nonzero_indices[0]
        return f"{i},1"

    # Special case: exactly one pile > 1.
    if len(bigs) == 1:
        i, x = bigs[0]
        # Let k be number of 1-heaps.
        k = ones
        # We want after move:
        # - if k is even, leave the big pile as 1, making total ones k+1 odd.
        # - if k is odd, remove the big pile entirely, leaving k ones odd.
        target = 1 if (k % 2 == 0) else 0
        take = x - target
        if 1 <= take <= x:
            return f"{i},{take}"

    # General case: play like normal Nim, making xor zero.
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

    # Fallback: if somehow xor is 0 (losing position) or no xor move found,
    # make the first legal move.
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"

    # Should never reach here unless all piles are zero.
    return "0,0"
