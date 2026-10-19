
def policy(piles: list[int]) -> str:
    # Ensure legality fallback
    def first_legal():
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"  # unreachable in valid nonterminal calls

    nonzero = [p for p in piles if p > 0]
    if not nonzero:
        return "0,0"  # terminal fallback, though arena should not call here

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big_count = len(big_indices)

    # Misère endgame: all nonzero piles are 1
    if ones == len(nonzero):
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Special misère case: exactly one pile > 1
    if big_count == 1:
        i = big_indices[0]
        big = piles[i]
        # Leave odd number of 1-heaps to opponent
        target = 1 if ones % 2 == 0 else 0
        take = big - target
        if 1 <= take <= big:
            return f"{i},{take}"
        return first_legal()

    # Normal Nim move: make xor zero
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

    # Losing position fallback: make any legal move
    return first_legal()
