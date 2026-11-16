
def policy(piles: list[int]) -> str:
    large_piles = [i for i, size in enumerate(piles) if size > 1]

    # Endgame where every nonempty pile contains exactly one object.
    if not large_piles:
        for i, size in enumerate(piles):
            if size > 0:
                return f"{i},1"

        # A terminal state should never be passed to the policy.
        return "0,1"

    # Misère endgame with exactly one pile larger than one.
    if len(large_piles) == 1:
        pile = large_piles[0]
        size = piles[pile]
        singleton_count = sum(1 for value in piles if value == 1)

        if singleton_count % 2 == 0:
            # Leave one object in the large pile, producing an odd
            # number of singleton piles.
            take = size - 1
        else:
            # Remove the large pile, preserving an odd singleton count.
            take = size

        return f"{pile},{take}"

    # With at least two large piles, ordinary Nim XOR play is optimal.
    nim_sum = 0
    for size in piles:
        nim_sum ^= size

    if nim_sum != 0:
        for i, size in enumerate(piles):
            target = size ^ nim_sum
            if target < size:
                return f"{i},{size - target}"

    # This is a losing position under perfect opposing play, but the move
    # remains legal and gives an imperfect opponent a chance to err.
    pile = max(range(4), key=lambda i: piles[i])
    return f"{pile},1"
