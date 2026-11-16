
def policy(piles: list[int]) -> str:
    """Return an optimal move for four-pile misère Nim."""
    nonempty = [i for i, size in enumerate(piles) if size > 0]

    # The game engine should not call the policy on a terminal state.
    if not nonempty:
        raise ValueError("No legal move exists in a terminal position")

    large = [i for i, size in enumerate(piles) if size > 1]
    singleton_count = sum(size == 1 for size in piles)

    # All remaining piles are singletons. Removing one is the only move type.
    if not large:
        return f"{nonempty[0]},1"

    # Enter the all-singleton endgame while leaving an odd number of
    # singletons to the opponent.
    if len(large) == 1:
        pile = large[0]
        size = piles[pile]

        if singleton_count % 2 == 0:
            # Leave this pile as one singleton.
            take = size - 1
        else:
            # Remove this pile completely.
            take = size

        return f"{pile},{take}"

    # With at least two large piles, ordinary Nim XOR play is optimal.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum != 0:
        for pile, size in enumerate(piles):
            target_size = size ^ nim_sum
            if target_size < size:
                return f"{pile},{size - target_size}"

    # XOR-zero positions are losing under perfect opposing play.
    # Still always provide a legal move.
    pile = nonempty[0]
    return f"{pile},1"
