
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misère Nim.
    Return format: 'pile,take'
    """

    def legal_move(i: int, take: int) -> str:
        if 0 <= i < len(piles) and 1 <= take <= piles[i]:
            return f"{i},{take}"
        # Emergency fallback for unexpected inputs / terminal states.
        for j, p in enumerate(piles):
            if p > 0:
                return f"{j},1"
        return "0,1"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big_count = len(big_indices)

    # Case 1: all nonzero heaps are size 1
    # Optimal rule: odd count is losing, even count is winning by removing one.
    if big_count == 0:
        for i, p in enumerate(piles):
            if p == 1:
                return legal_move(i, 1)
        # Terminal fallback (should normally never be queried)
        return "0,1"

    # Case 2: exactly one heap > 1
    # Make all remaining nonzero heaps be 1-heaps, leaving an odd count to opponent.
    if big_count == 1:
        i = big_indices[0]
        if ones % 2 == 0:
            # Leave this heap as 1
            return legal_move(i, piles[i] - 1)
        else:
            # Remove this heap completely
            return legal_move(i, piles[i])

    # Case 3: at least two heaps > 1
    # Play normal Nim: move to xor = 0 when possible.
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                return legal_move(i, p - target)

    # Case 4: theoretically losing position under perfect play.
    # No winning move exists, but return a legal move.
    # Heuristic: reduce a large pile to 1 to create a tricky misère endgame.
    for i, p in enumerate(piles):
        if p > 1:
            return legal_move(i, p - 1)

    for i, p in enumerate(piles):
        if p > 0:
            return legal_move(i, 1)

    return "0,1"
