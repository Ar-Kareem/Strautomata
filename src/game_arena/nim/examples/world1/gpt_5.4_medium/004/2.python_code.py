
def policy(piles: list[int]) -> str:
    def fallback_move() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal state should not be given to the policy.
        return "0,1"

    nonzero = [p for p in piles if p > 0]
    if not nonzero:
        return "0,1"  # Unreachable in a valid game call.

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big_count = len(big_indices)

    # Case 1: all non-empty piles are size 1
    if big_count == 0:
        return fallback_move()

    # Case 2: exactly one pile larger than 1
    if big_count == 1:
        i = big_indices[0]
        heap = piles[i]
        # Leave an odd number of 1-heaps to the opponent.
        take = heap - 1 if ones % 2 == 0 else heap
        if 1 <= take <= heap:
            return f"{i},{take}"
        return fallback_move()

    # Case 3: at least two piles larger than 1 -> normal Nim move to xor 0
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

    # Losing position or safety fallback
    return fallback_move()
