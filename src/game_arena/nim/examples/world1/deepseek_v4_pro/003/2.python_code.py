
def policy(piles: list[int]) -> str:
    # Count piles > 1 and piles == 1
    gt_one = 0
    ones = 0
    for p in piles:
        if p > 1:
            gt_one += 1
        elif p == 1:
            ones += 1

    # Case 1: all piles are 0 or 1
    if gt_one == 0:
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # Fallback (should never be reached in a live game)
        return "0,0"

    # Case 2: exactly one pile > 1
    if gt_one == 1:
        for i, p in enumerate(piles):
            if p > 1:
                if ones % 2 == 1:
                    # Leave 0 objects in this pile -> take all
                    return f"{i},{p}"
                else:
                    # Leave 1 object in this pile -> take p-1
                    return f"{i},{p-1}"

    # Case 3: two or more piles > 1 -> normal Nim
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Losing position: any legal move
    if nim_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Winning position: make nim_sum zero
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            return f"{i},{take}"

    # Fallback
    return "0,0"
