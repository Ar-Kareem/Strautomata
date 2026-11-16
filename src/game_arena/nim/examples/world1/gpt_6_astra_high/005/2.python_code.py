
def policy(piles: list[int]) -> str:
    """Return an optimal misere-Nim move for a nonterminal position."""
    largest = max(range(4), key=lambda i: piles[i])

    if piles[largest] == 0:
        raise ValueError("The terminal position has no legal move.")

    large = [i for i, size in enumerate(piles) if size > 1]

    # Only singleton piles remain: every legal move is equivalent.
    if not large:
        return f"{largest},1"

    # Leave an odd number of singleton piles to the opponent.
    if len(large) == 1:
        i = large[0]
        singles = sum(size == 1 for size in piles)
        target = 1 if singles % 2 == 0 else 0
        return f"{i},{piles[i] - target}"

    # With at least two large piles, use the ordinary Nim XOR rule.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum:
        for i, size in enumerate(piles):
            target = size ^ nim_sum
            if target < size:
                return f"{i},{size - target}"

    # Losing against perfect play, but this move is always legal.
    return f"{largest},1"
