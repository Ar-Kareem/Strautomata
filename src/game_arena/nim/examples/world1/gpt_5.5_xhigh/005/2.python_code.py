
def policy(piles: list[int]) -> str:
    vals = [int(p) for p in piles]

    def legal_move(i: int, take: int) -> str:
        if 0 <= i < len(vals) and 1 <= take <= vals[i]:
            return f"{i},{take}"
        # Emergency fallback for any unexpected input.
        for j, p in enumerate(vals):
            if p > 0:
                return f"{j},1"
        # Terminal states should not be queried; no legal move exists here.
        return "0,0"

    xor_sum = 0
    ones = 0
    large = []
    first_nonzero = None

    for i, p in enumerate(vals):
        xor_sum ^= p
        if p > 0 and first_nonzero is None:
            first_nonzero = i
        if p == 1:
            ones += 1
        elif p > 1:
            large.append(i)

    # No legal move exists in a terminal state; this should be unreachable.
    if first_nonzero is None:
        return "0,0"

    # Endgame: every non-empty pile is size 1.
    # Winning iff the number of 1-piles is even; take one to leave odd.
    if not large:
        return legal_move(first_nonzero, 1)

    # Misere Nim special case: exactly one pile bigger than 1.
    # Leave the opponent an odd number of 1-piles.
    if len(large) == 1:
        i = large[0]
        h = vals[i]
        if ones % 2 == 0:
            # Turn the large pile into a single 1-pile.
            return legal_move(i, h - 1)
        else:
            # Remove the large pile entirely.
            return legal_move(i, h)

    # With at least two large piles, play normal Nim: move to xor 0.
    if xor_sum != 0:
        for i, p in enumerate(vals):
            target = p ^ xor_sum
            if target < p:
                return legal_move(i, p - target)

    # Losing position under perfect play. Any legal move is minimax-equivalent.
    # Prefer a move that creates a tricky one-large-pile state when possible.
    if len(large) == 2:
        i = min(large, key=lambda j: (vals[j], j))
        return legal_move(i, vals[i] - 1)

    # Otherwise, keep the position as large/complex as possible.
    i = max(large, key=lambda j: (vals[j], -j))
    return legal_move(i, 1)
