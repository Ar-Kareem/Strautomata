
def policy(piles: list[int]) -> str:
    """Return an optimal misere Nim move for a nonterminal position."""
    large = [i for i, size in enumerate(piles) if size > 1]

    if len(large) == 1:
        i = large[0]
        ones = sum(size == 1 for size in piles)
        remaining = 1 if ones % 2 == 0 else 0
        return f"{i},{piles[i] - remaining}"

    if len(large) >= 2:
        nim_sum = 0
        for size in piles:
            nim_sum ^= size

        if nim_sum:
            for i, size in enumerate(piles):
                remaining = size ^ nim_sum
                if remaining < size:
                    return f"{i},{size - remaining}"

    # All piles are singletons, or this is a losing XOR-zero position.
    for i, size in enumerate(piles):
        if size > 0:
            return f"{i},1"

    # Terminal positions have no legal move and must not be queried.
    raise ValueError("No legal move exists: all piles are empty.")
