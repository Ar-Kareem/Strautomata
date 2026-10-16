
def policy(piles: list[int]) -> str:
    # Count piles greater than 1
    count_gt1 = sum(1 for p in piles if p > 1)
    
    if count_gt1 == 0:
        # All piles are 1 (and we have 4 piles, even) — we win by taking one
        return "0,1"
    elif count_gt1 == 1:
        # Exactly one pile > 1: take the entire pile to leave three 1s (odd)
        for i in range(4):
            if piles[i] > 1:
                return f"{i},{piles[i]}"
    else:
        # count_gt1 >= 2: use normal nim strategy
        xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
        if xor_sum == 0:
            # Losing position, make any legal move (take 1 from first non-zero)
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Find a move to make xor_sum 0
            for i in range(4):
                target = piles[i] ^ xor_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
    
    # Fallback: should not occur, but for safety
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
