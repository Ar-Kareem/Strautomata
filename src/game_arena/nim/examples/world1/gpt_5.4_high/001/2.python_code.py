
def policy(piles: list[int]) -> str:
    """
    Perfect-play policy for 4-pile misère Nim.
    Returns a move as 'pile,take'.
    """

    def first_legal_move() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal states should not be passed in, but keep a safe fallback.
        return "0,1"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all non-empty piles are size 1
    if not big_indices:
        return first_legal_move()

    # Case 2: exactly one pile is larger than 1
    if len(big_indices) == 1:
        i = big_indices[0]
        p = piles[i]
        # Leave an odd number of 1-heaps to the opponent.
        take = p - 1 if (ones % 2 == 0) else p
        if 1 <= take <= p:
            return f"{i},{take}"
        return first_legal_move()

    # Case 3: at least two piles are larger than 1 -> normal Nim move to xor 0
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Losing position under perfect play: return any legal move
    return first_legal_move()
