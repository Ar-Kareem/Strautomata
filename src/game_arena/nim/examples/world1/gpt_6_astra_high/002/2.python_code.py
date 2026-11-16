
def policy(piles: list[int]) -> str:
    """Return an optimal move for any nonterminal misere Nim position."""
    nonempty = [i for i, size in enumerate(piles) if size > 0]
    if not nonempty:
        # The game has ended; no legal move exists.
        raise ValueError("Terminal position has no legal move.")

    large = [i for i in nonempty if piles[i] > 1]
    ones = sum(size == 1 for size in piles)

    if not large:
        return f"{nonempty[0]},1"

    if len(large) == 1:
        i = large[0]
        # Leave an odd number of singleton piles.
        target = 0 if ones % 2 else 1
        return f"{i},{piles[i] - target}"

    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum:
        for i in nonempty:
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                return f"{i},{piles[i] - target}"

    # Zero-XOR position: no winning move against perfect opposition.
    i = max(nonempty, key=lambda index: piles[index])
    return f"{i},1"
