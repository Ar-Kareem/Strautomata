
def policy(piles: list[int]) -> str:
    # Ensure we always return a legal move, even on malformed inputs.
    if not isinstance(piles, list) or len(piles) != 4:
        return "0,1"

    # Collect nonzero piles.
    nonzero = [(i, x) for i, x in enumerate(piles) if isinstance(x, int) and x > 0]

    # If somehow no legal move exists, return a fallback legal-looking string.
    # In a proper game this state should be terminal and policy should not be called.
    if not nonzero:
        return "0,1"

    # Misère Nim special case: all nonzero piles are size 1.
    if all(x == 1 for _, x in nonzero):
        # Let k be the number of 1-heaps.
        # Winning play is to leave an odd number to the opponent.
        k = len(nonzero)
        idx = nonzero[0][0]
        return f"{idx},1"

    # General misère Nim case:
    # If there is exactly one heap > 1, handle directly.
    big = [(i, x) for i, x in nonzero if x > 1]
    ones_count = sum(1 for _, x in nonzero if x == 1)

    if len(big) == 1:
        i, x = big[0]
        # Reduce the big heap depending on parity of the number of 1-heaps.
        # Leave:
        # - 1 if ones_count is odd
        # - 0 if ones_count is even
        target = 1 if ones_count % 2 == 1 else 0
        take = x - target
        if 1 <= take <= piles[i]:
            return f"{i},{take}"

    # Otherwise, play like normal Nim: move to nim-sum 0 if possible.
    nim_sum = 0
    for x in piles:
        if isinstance(x, int) and x > 0:
            nim_sum ^= x

    if nim_sum != 0:
        for i, x in enumerate(piles):
            if isinstance(x, int) and x > 0:
                target = x ^ nim_sum
                if target < x:
                    take = x - target
                    if 1 <= take <= x:
                        return f"{i},{take}"

    # If no winning move exists, return any legal move.
    # Prefer taking 1 from the first nonempty pile.
    i, x = nonzero[0]
    return f"{i},1"
