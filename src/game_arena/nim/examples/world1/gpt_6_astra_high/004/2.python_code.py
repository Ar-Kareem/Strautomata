
def policy(piles: list[int]) -> str:
    large = [i for i, size in enumerate(piles) if size > 1]
    ones = sum(size == 1 for size in piles)

    if len(large) == 1:
        i = large[0]
        # Leave an odd number of singletons for the opponent.
        remaining = 0 if ones % 2 else 1
        return f"{i},{piles[i] - remaining}"

    if len(large) >= 2:
        nim_sum = 0
        for size in piles:
            nim_sum ^= size

        if nim_sum:
            for i, size in enumerate(piles):
                target = size ^ nim_sum
                if target < size:
                    return f"{i},{size - target}"

    # Only singletons remain, or this is a losing XOR-zero position.
    for i, size in enumerate(piles):
        if size > 0:
            return f"{i},1"

    # Terminal positions have no legal move and should not call policy.
    raise ValueError("No legal move: all piles are empty.")
