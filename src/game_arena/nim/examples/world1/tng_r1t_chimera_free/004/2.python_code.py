
def policy(piles: list[int]) -> str:
    non_zero = [p for p in piles if p > 0]
    if len(non_zero) == 1:
        pile_size = non_zero[0]
        pile_index = piles.index(pile_size)
        if pile_size == 1:
            return f"{pile_index},1"
        else:
            return f"{pile_index},{pile_size - 1}"
    else:
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        if nim_sum != 0:
            for i in range(len(piles)):
                pile_size = piles[i]
                if pile_size == 0:
                    continue
                target = pile_size ^ nim_sum
                if target < pile_size:
                    take = pile_size - target
                    return f"{i},{take}"
        # If no winning move (nim_sum is zero), take 1 from the largest pile
        max_size = max(piles)
        for i in range(len(piles)):
            if piles[i] == max_size:
                return f"{i},1"
