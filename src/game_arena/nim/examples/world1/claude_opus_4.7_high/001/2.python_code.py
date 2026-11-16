
def policy(piles: list[int]) -> str:
    piles = list(piles)
    count_big = sum(1 for p in piles if p >= 2)
    ones = sum(1 for p in piles if p == 1)

    # Case 1: all piles are 0 or 1
    if count_big == 0:
        for i, p in enumerate(piles):
            if p >= 1:
                return f"{i},1"
        # Fallback (shouldn't occur in legal game state)
        return "0,1"

    # Case 2: exactly one pile has size >= 2
    if count_big == 1:
        big_idx = next(i for i, p in enumerate(piles) if p >= 2)
        big = piles[big_idx]
        if ones % 2 == 0:
            # leave big as 1 -> opponent faces odd count of 1s
            return f"{big_idx},{big - 1}"
        else:
            # take whole big pile -> opponent faces odd count of 1s
            return f"{big_idx},{big}"

    # Case 3: two or more big piles -> standard Nim
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if take >= 1:
                    return f"{i},{take}"

    # Losing position (XOR == 0): make a minimal move from largest pile
    max_idx = 0
    for i, p in enumerate(piles):
        if p > piles[max_idx]:
            max_idx = i
    if piles[max_idx] >= 1:
        return f"{max_idx},1"

    # Fallback
    for i, p in enumerate(piles):
        if p >= 1:
            return f"{i},1"
    return "0,1"
