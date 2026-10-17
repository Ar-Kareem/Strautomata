
def policy(piles: list[int]) -> str:
    """Return an optimal legal move for four-pile misère Nim."""
    large = [i for i, size in enumerate(piles) if size > 1]
    singletons = sum(size == 1 for size in piles)

    # All remaining piles contain one object.
    if not large:
        for i, size in enumerate(piles):
            if size > 0:
                return f"{i},1"

    # Exactly one large pile: leave an odd number of singleton piles.
    if len(large) == 1:
        i = large[0]
        target = 1 if singletons % 2 == 0 else 0
        return f"{i},{piles[i] - target}"

    # With at least two large piles, use the normal Nim XOR strategy.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum:
        for i, size in enumerate(piles):
            target = size ^ nim_sum
            if target < size:
                return f"{i},{size - target}"

    # This is a losing position under perfect play; any legal move is optimal.
    for i, size in enumerate(piles):
        if size > 0:
            return f"{i},1"

    raise ValueError("No legal move exists in a terminal position.")
