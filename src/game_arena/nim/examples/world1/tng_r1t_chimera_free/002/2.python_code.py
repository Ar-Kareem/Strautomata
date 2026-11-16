
def policy(piles: list[int]) -> str:
    # Calculate the nim-sum of all piles
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    # Check if all non-zero piles are 1 (for misère case)
    all_ones = all(p == 0 or p == 1 for p in piles)
    
    if nim_sum != 0:
        # Find a pile to adjust to make nim-sum zero
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
        # Fallback (should not be reached if piles are valid)
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        if all_ones:
            # Handle losing position: take 1 from first non-zero pile
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # Take 1 from first pile with more than 1 object
            for i in range(4):
                if piles[i] > 1:
                    return f"{i},1"
            # If all remaining piles are 0 or 1, take 1 from first non-zero
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
    # Fallback (shouldn't be reached)
    return "0,1"
