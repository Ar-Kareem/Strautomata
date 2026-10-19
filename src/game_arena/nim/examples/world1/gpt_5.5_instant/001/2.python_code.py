
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    Last player to take an object loses.
    """
    # Defensive normalization: arena should provide length 4 nonnegative ints.
    piles = [int(x) for x in piles]

    # Legal fallback in any non-terminal state.
    def fallback() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal should not be queried; return a syntactically valid move impossible to make.
        # This branch is only for API totality.
        return "0,1"

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return fallback()

    big = [(i, p) for i, p in nonzero if p > 1]
    ones_count = sum(1 for p in piles if p == 1)

    # Endgame: all remaining piles are size 1.
    # With k ones, taking one leaves k-1 ones.
    # In misere Nim, positions with odd k are winning for player to move,
    # so from even k we are losing; still take one legally.
    if not big:
        return f"{nonzero[0][0]},1"

    # Special misere case: exactly one pile larger than 1.
    # Choose from the big pile so that the opponent receives an odd number
    # of size-1 piles, which is losing for them.
    if len(big) == 1:
        i, p = big[0]
        # If current number of ones is even, reduce big pile to 1:
        # opponent sees ones_count + 1, odd.
        # If current number of ones is odd, remove the whole big pile:
        # opponent sees ones_count, odd.
        if ones_count % 2 == 0:
            take = p - 1
            if take >= 1:
                return f"{i},{take}"
            return fallback()
        else:
            return f"{i},{p}"

    # General case: at least two piles larger than 1.
    # Normal Nim xor move is optimal unless it transitions into the all-ones
    # region, which cannot happen here except potentially handled above after
    # reducing one pile; with two or more big piles before moving, one move
    # cannot make all piles <= 1 unless exactly two big piles and one is changed,
    # so normal xor remains the standard optimal misere play.
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

    # Losing position under perfect play: return any legal move.
    return fallback()
