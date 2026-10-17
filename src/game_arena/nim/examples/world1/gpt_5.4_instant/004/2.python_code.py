
def policy(piles: list[int]) -> str:
    # Misère Nim optimal play for 4 piles.
    # Returns a legal move string "pile,take".

    # Defensive legality fallback
    def first_legal(ps):
        for i, x in enumerate(ps):
            if x > 0:
                return f"{i},1"
        return "0,0"  # unreachable in legal nonterminal calls

    # Count pile types
    nonzero = [x for x in piles if x > 0]
    if not nonzero:
        return "0,0"  # terminal fallback; should not be called

    ones = sum(1 for x in piles if x == 1)
    big_indices = [i for i, x in enumerate(piles) if x > 1]
    big_count = len(big_indices)

    # Case 1: all nonzero heaps are size 1
    if ones == len(nonzero):
        # In misère Nim with all ones, leave an odd number of heaps to opponent.
        # If n is even, take 1 heap; if n is odd, forced losing, still take 1 heap.
        for i, x in enumerate(piles):
            if x == 1:
                return f"{i},1"

    # Case 2: exactly one heap > 1
    if big_count == 1:
        i = big_indices[0]
        x = piles[i]
        # Leave odd number of 1-heaps to opponent.
        # After reducing heap i to r in {0,1}, opponent sees ones + r heaps of size 1.
        # Choose odd total if possible.
        if ones % 2 == 0:
            # want ones + r odd => r = 1
            take = x - 1
            if take >= 1:
                return f"{i},{take}"
            else:
                return first_legal(piles)
        else:
            # want ones + r odd => r = 0
            take = x
            if take >= 1:
                return f"{i},{take}"
            else:
                return first_legal(piles)

    # Case 3: at least two heaps > 1
    # Play normal Nim: move to xor 0.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(piles):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # If already xor 0 (losing position), make any legal move.
    return first_legal(piles)
