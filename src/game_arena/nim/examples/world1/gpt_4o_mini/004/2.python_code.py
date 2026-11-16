
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If the nim_sum is 0, there are no winning moves; pick a pile and remove one object
    if nim_sum == 0:
        for i in range(len(piles)):
            if piles[i] > 0:
                return f"{i},1"

    # Otherwise, find a move that makes nim_sum == 0
    for i in range(len(piles)):
        if piles[i] > 0:
            # Calculate what would happen if we took (piles[i] - new_pile_value)
            new_pile_value = piles[i] ^ nim_sum
            if new_pile_value < piles[i]:
                take = piles[i] - new_pile_value
                return f"{i},{take}"

    # Fallback: Should not reach here if above logic is correct
    return "0,1"  # Just a default move in case of unexpected state
