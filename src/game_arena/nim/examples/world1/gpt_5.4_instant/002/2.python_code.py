
def policy(piles: list[int]) -> str:
    # Ensure we always return a legal move string.
    n = list(piles[:4]) + [0] * max(0, 4 - len(piles))
    n = n[:4]

    nonzero = [i for i, x in enumerate(n) if x > 0]
    if not nonzero:
        return "0,0"  # Should never be used in a live nonterminal state.

    ones = sum(1 for x in n if x == 1)
    big_indices = [i for i, x in enumerate(n) if x > 1]
    big_count = len(big_indices)

    # Misère special case: all nonzero piles are 1
    if big_count == 0:
        # Leave an odd number of 1-heaps to opponent.
        # If m nonzero heaps all of size 1:
        # - m even: take 1 heap, leave odd -> winning
        # - m odd: any move loses; still return legal move
        i = nonzero[0]
        return f"{i},1"

    # Misère special case: exactly one heap > 1
    if big_count == 1:
        i = big_indices[0]
        k = ones
        # Reduce big heap to 1 if k is even, else to 0.
        target = 1 if (k % 2 == 0) else 0
        take = n[i] - target
        if 1 <= take <= n[i]:
            return f"{i},{take}"

    # General case: play normal Nim, move to xor 0
    xor_sum = 0
    for x in n:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(n):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # Fallback: remove 1 from first nonempty pile
    i = nonzero[0]
    return f"{i},1"
