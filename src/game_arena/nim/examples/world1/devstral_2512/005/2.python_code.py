
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (bitwise XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If Nim-sum is zero, we're in a losing position - make any legal move
    if nim_sum == 0:
        # Find the first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                # Take 1 object (or more if it's the last pile)
                take = 1
                if sum(piles) == piles[i]:  # Only one pile left
                    take = max(1, piles[i] - 1)  # Leave at least 1 to avoid losing
                return f"{i},{take}"

    # Otherwise, find a winning move
    for i in range(4):
        if piles[i] > 0:
            # Calculate what the pile should be to make Nim-sum zero
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"

    # Fallback (should never reach here for valid Nim positions)
    return "0,1"
