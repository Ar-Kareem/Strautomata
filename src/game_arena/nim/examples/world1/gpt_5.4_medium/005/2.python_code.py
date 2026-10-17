
def policy(piles: list[int]) -> str:
    def first_legal_move() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal state should not be queried; no legal move exists.
        return "0,1"

    # Count heap types
    ones = 0
    big_indices = []
    for i, p in enumerate(piles):
        if p == 1:
            ones += 1
        elif p > 1:
            big_indices.append(i)

    big_count = len(big_indices)

    # Case 1: all nonempty heaps are size 1
    if big_count == 0:
        return first_legal_move()

    # Case 2: exactly one heap is larger than 1
    if big_count == 1:
        i = big_indices[0]
        p = piles[i]
        target = 0 if (ones % 2 == 1) else 1
        take = p - target
        if take >= 1:
            return f"{i},{take}"
        return first_legal_move()

    # Case 3: at least two heaps > 1 -> normal Nim move to xor 0
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Losing position or unexpected issue: return any legal move
    return first_legal_move()
