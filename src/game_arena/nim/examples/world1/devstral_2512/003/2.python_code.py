
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If Nim-sum is zero, any move is acceptable (but we'll still try to make a smart move)
    if nim_sum == 0:
        # Find the first non-zero pile and take 1 object
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Find the pile to modify to make the Nim-sum zero
        for i in range(4):
            if (piles[i] ^ nim_sum) < piles[i]:
                take = piles[i] - (piles[i] ^ nim_sum)
                return f"{i},{take}"

    # Fallback: take 1 from the first non-zero pile (shouldn't reach here if piles are non-zero)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
