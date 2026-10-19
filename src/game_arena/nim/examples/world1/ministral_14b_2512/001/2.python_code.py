
def policy(piles: list[int]) -> str:
    # Calculate Nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # Case 1: Nim-sum is non-zero (standard Nim strategy)
    if nim_sum != 0:
        for i in range(4):
            if piles[i] > 0:
                target = nim_sum ^ piles[i]
                if target < piles[i]:
                    return f"{i},{piles[i] - target}"
    else:
        # Case 2: Nim-sum is zero (misère Nim strategy)
        # Subcase 2.1: All piles are 1 (must leave odd number of piles)
        if all(pile == 1 for pile in piles):
            # Take all but one pile (if possible)
            for i in range(4):
                if piles[i] == 1:
                    continue
                else:
                    return f"{i},{piles[i] - 1}"
            # If all piles are 1, take all but one (but this is impossible since all are 1)
            # So take from any pile (but this is a losing position, so just take 1 from any pile)
            return f"0,1"
        else:
            # Subcase 2.2: Not all piles are 1, try to leave all piles as 1
            # Find a pile where we can reduce it to 1
            for i in range(4):
                if piles[i] > 1:
                    return f"{i},{piles[i] - 1}"
            # If all piles are 1, this is a losing position (should not happen due to earlier check)
            return f"0,1"

    # Fallback (should not reach here if logic is correct)
    return "0,1"
