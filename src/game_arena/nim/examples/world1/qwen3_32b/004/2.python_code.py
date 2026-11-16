
def policy(piles: list[int]) -> str:
    xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    if xor_sum != 0:
        # Standard Nim strategy to make nim-sum zero
        for i in range(4):
            pile_size = piles[i]
            take = pile_size ^ xor_sum
            if take < pile_size:
                return f"{i},{pile_size - take}"
    
    else:
        # Handle all-ones case with even number of piles
        if all(p == 1 for p in piles):
            return "0,1"
        # Otherwise, take 1 from the first non-zero pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # This line is unreachable for valid inputs
    return "0,1"
