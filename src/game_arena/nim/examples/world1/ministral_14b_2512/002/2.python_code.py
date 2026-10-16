
def policy(piles: list[int]) -> str:
    # Check if all piles are 1 (special case for misère Nim)
    if all(p == 1 for p in piles):
        # Take from all but one pile (e.g., take 1 from piles 0, 1, 2, leaving pile 3)
        # We can take from any three piles, leaving one pile of 1
        # Here, we take from piles 0, 1, 2 (arbitrary choice)
        return "0,1"

    # Compute Nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum != 0:
        # Find a move that leaves Nim-sum 0
        for i in range(4):
            if piles[i] > 0:
                target = nim_sum ^ piles[i]
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
    else:
        # Nim-sum is 0, so we are in a losing position (assuming opponent plays optimally)
        # We must make a move that doesn't immediately lose (e.g., take 1 from any pile)
        # This is not optimal but necessary to avoid disqualification
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"

    # Fallback (should not reach here for valid inputs)
    return "0,1"
