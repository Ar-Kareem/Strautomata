
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    if nim_sum != 0:
        for i, pile in enumerate(piles):
            target = nim_sum ^ pile
            if target < pile:
                take = pile - target
                return f"{i},{take}"
    else:
        # Find the largest pile (first occurrence if tied)
        max_index = 0
        max_val = piles[0]
        for i in range(1, len(piles)):
            if piles[i] > max_val:
                max_val = piles[i]
                max_index = i
        return f"{max_index},1"
