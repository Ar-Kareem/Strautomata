
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Action format: 'pile,take'
    Rule: player who takes the last object loses.
    """

    # Find non-empty piles; terminal states should not be queried.
    nonzero = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return "0,1"  # No legal move exists in a terminal state.

    large = [i for i, p in enumerate(piles) if p > 1]

    # Endgame: all remaining piles are size 1.
    # If the number of ones is even, this is winning; if odd, losing.
    # In either case the only legal type of move is to take one.
    if not large:
        return f"{nonzero[0]},1"

    # Special misere case: exactly one pile larger than 1.
    # Leave the opponent an odd number of 1-piles, which is losing for them.
    if len(large) == 1:
        i = large[0]
        ones = sum(1 for p in piles if p == 1)

        # If ones is even, reduce the large pile to 1.
        # If ones is odd, remove the large pile entirely.
        target = 1 if ones % 2 == 0 else 0
        take = piles[i] - target

        if take >= 1:
            return f"{i},{take}"

    # General case: at least two piles larger than 1.
    # Normal Nim xor-zero move is optimal.
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

    # Losing position fallback: make a legal move.
    # Prefer reducing the largest pile by 1 to preserve complexity.
    i = max(nonzero, key=lambda idx: piles[idx])
    return f"{i},1"
