
def policy(piles: list[int]) -> str:
    xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if xor_sum != 0:
        # Check if only one pile has stones
        count_non_zero = sum(1 for p in piles if p != 0)
        if count_non_zero == 1:
            # Only one pile left, avoid taking all if possible
            for i in range(4):
                if piles[i] > 0:
                    if piles[i] == 1:
                        return f"{i},1"
                    else:
                        return f"{i},{piles[i] - 1}"
        else:
            # Standard Nim move to balance nim_sum to zero
            for i in range(4):
                desired = piles[i] ^ xor_sum
                if piles[i] > desired:
                    take = piles[i] - desired
                    return f"{i},{take}"
    else:
        # Nim-sum is zero, force opponent to take last object
        for i in range(4):
            if piles[i] > 1:
                return f"{i},{piles[i]}"
        # All piles are 0 or 1, force opponent to take last object
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    # Fallback (should not occur in valid game)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
