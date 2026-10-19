
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If Nim-sum is zero, make a random legal move (since any move is losing)
    if nim_sum == 0:
        # Find the first non-zero pile and take 1 object
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Find the pile to modify
        for i in range(4):
            if (piles[i] ^ nim_sum) < piles[i]:
                take = piles[i] - (piles[i] ^ nim_sum)
                return f"{i},{take}"

    # Fallback: if no move found (shouldn't happen for valid piles)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
