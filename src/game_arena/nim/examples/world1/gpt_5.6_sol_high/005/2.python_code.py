
def policy(piles: list[int]) -> str:
    large_piles = [i for i, size in enumerate(piles) if size > 1]

    # Endgame: all nonempty piles contain exactly one object.
    if not large_piles:
        for i, size in enumerate(piles):
            if size > 0:
                return f"{i},1"

    # Misère endgame transition: exactly one large pile remains.
    if len(large_piles) == 1:
        i = large_piles[0]
        singletons = sum(size == 1 for size in piles)

        # Leave an odd number of singleton piles to the opponent.
        target_size = 1 if singletons % 2 == 0 else 0
        take = piles[i] - target_size
        return f"{i},{take}"

    # With at least two large piles, ordinary Nim strategy is optimal.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum != 0:
        for i, size in enumerate(piles):
            target_size = size ^ nim_sum
            if target_size < size:
                return f"{i},{size - target_size}"

    # No winning move exists; return a legal move.
    for i, size in enumerate(piles):
        if size > 0:
            return f"{i},1"

    # The arena should never call policy after the game has ended.
    raise ValueError("No legal move exists in a terminal position")
