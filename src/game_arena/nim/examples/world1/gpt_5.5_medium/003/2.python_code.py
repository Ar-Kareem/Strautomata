
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Last player to take an object loses.
    - Return format: 'pile,take'.
    """

    def make_move(i: int, take: int) -> str:
        return f"{i},{take}"

    # Terminal states should not be passed to the policy because no legal move
    # exists. Return a harmless fallback string rather than raising.
    if not any(piles):
        return "0,0"

    ones = sum(1 for x in piles if x == 1)
    big_indices = [i for i, x in enumerate(piles) if x > 1]
    num_big = len(big_indices)

    # Case 1: all remaining piles are size 0 or 1.
    # In misere Nim, odd number of ones is losing, even number is winning.
    if num_big == 0:
        for i, x in enumerate(piles):
            if x == 1:
                return make_move(i, 1)

    # Case 2: exactly one pile larger than 1.
    # Reduce it so that the opponent faces an odd number of 1-piles.
    if num_big == 1:
        i = big_indices[0]

        # If current number of ones is even, leave the big pile as 1.
        # If current number of ones is odd, remove the big pile entirely.
        target = 1 if ones % 2 == 0 else 0
        take = piles[i] - target

        if take >= 1:
            return make_move(i, take)

    # Compute xor for standard Nim logic.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    # Case 3: multiple large piles and xor is nonzero.
    # Standard Nim move to make xor zero is optimal here.
    if xor_sum != 0:
        for i, x in enumerate(piles):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if take >= 1:
                    return make_move(i, take)

    # Case 4: losing position under perfect play.
    # Any legal move loses against a perfect opponent, but we still must return
    # a legal move. Removing a whole large pile often punishes weaker policies.
    if big_indices:
        i = min(big_indices, key=lambda idx: piles[idx])
        return make_move(i, piles[i])

    # Final legal fallback.
    for i, x in enumerate(piles):
        if x > 0:
            return make_move(i, 1)

    return "0,0"
