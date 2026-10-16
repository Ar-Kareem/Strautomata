
def policy(piles: list[int]) -> str:
    def first_legal_move() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal states should not be queried in a valid game.
        # Fallback string; unreachable in proper arena usage.
        return "0,0"

    nonzero = [p for p in piles if p > 0]
    if not nonzero:
        return first_legal_move()

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big = len(big_indices)

    # Case 1: all nonzero piles are 1
    if big == 0:
        return first_legal_move()

    # Case 2: exactly one pile > 1
    if big == 1:
        i = big_indices[0]
        target = 1 if (ones % 2 == 0) else 0
        take = piles[i] - target
        if take >= 1:
            return f"{i},{take}"
        return first_legal_move()

    # Case 3: at least two piles > 1 -> normal Nim move to xor 0 if possible
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            new_p = p ^ x
            if new_p < p:
                take = p - new_p
                if take >= 1:
                    return f"{i},{take}"

    # Losing position or safety fallback
    return first_legal_move()
