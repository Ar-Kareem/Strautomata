
"""Optimal policy for four-pile misère Nim."""


def policy(piles: list[int]) -> str:
    """Return an optimal legal move in 'pile,take' format."""
    nonempty = [i for i, size in enumerate(piles) if size > 0]
    if not nonempty:
        raise ValueError("No legal move exists in a terminal state")

    large = [i for i, size in enumerate(piles) if size > 1]

    # Every remaining pile has size 1. The only possible move is to take one.
    if not large:
        return f"{nonempty[0]},1"

    # Misère endgame: exactly one pile is larger than 1.
    if len(large) == 1:
        pile = large[0]
        one_piles = sum(size == 1 for size in piles)

        # Leave an odd number of one-object piles to the opponent.
        target_size = 1 if one_piles % 2 == 0 else 0
        take = piles[pile] - target_size
        return f"{pile},{take}"

    # With at least two large piles, ordinary Nim XOR strategy is optimal.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum != 0:
        for pile, size in enumerate(piles):
            target_size = size ^ nim_sum
            if target_size < size:
                return f"{pile},{size - target_size}"

    # This is a losing position under perfect play, but the move remains legal.
    pile = nonempty[0]
    return f"{pile},1"
