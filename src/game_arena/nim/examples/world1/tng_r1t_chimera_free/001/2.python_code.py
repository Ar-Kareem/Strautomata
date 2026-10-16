
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    if nim_sum != 0:
        for i, pile in enumerate(piles):
            target = pile ^ nim_sum
            if target < pile:
                take = pile - target
                return f"{i},{take}"
    # If all XOR to zero, take 1 from the first non-zero pile
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    return "0,1"  # Should not reach as game ends when all piles are zero
