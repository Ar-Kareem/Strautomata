
def policy(piles: list[int]) -> str:
    """Return an optimal move for four-pile misère Nim."""

    big_piles = [i for i, p in enumerate(piles) if p > 1]

    # Endgame: only zero or one object remains in every pile.
    # Every legal move removes one singleton pile. Leaving an odd
    # number of singleton piles is winning; if the current count
    # is odd, all moves are equivalent under perfect play.
    if not big_piles:
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"

        # A terminal position should never be passed to policy.
        # No legal move exists in that case, but retain a valid-format
        # fallback for robustness.
        return "0,1"

    # With exactly one large pile, move directly to the losing
    # all-singleton endgame: leave an odd number of 1-piles.
    if len(big_piles) == 1:
        i = big_piles[0]
        singleton_count = sum(1 for p in piles if p == 1)

        # If the existing singleton count is even, make this pile 1.
        # If it is odd, remove the large pile completely.
        target = 1 if singleton_count % 2 == 0 else 0
        return f"{i},{piles[i] - target}"

    # Outside the special endgame, misère Nim P-positions are exactly
    # positions whose bitwise XOR is zero.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                # At least one other pile larger than 1 remains, so this
                # is a valid move to a genuine zero-XOR P-position.
                return f"{i},{p - target}"

    # The current position is already losing under perfect play.  Prefer
    # clearing one of two large piles, leaving a single-large-pile position
    # where common normal-Nim policies often make the wrong endgame move.
    if len(big_piles) == 2:
        i = min(big_piles, key=lambda j: piles[j])
        return f"{i},{piles[i]}"

    # Otherwise, make a conservative legal move.
    i = max(big_piles, key=lambda j: piles[j])
    return f"{i},1"
