
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If Nim-sum is zero, make a random legal move (take 1 from the first non-empty pile)
    if nim_sum == 0:
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"

    # Find the pile to modify
    for i in range(4):
        if (piles[i] ^ nim_sum) < piles[i]:
            take = piles[i] - (piles[i] ^ nim_sum)
            return f"{i},{take}"

    # Fallback: take 1 from the first non-empty pile (should theoretically never reach here if Nim-sum is non-zero)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
