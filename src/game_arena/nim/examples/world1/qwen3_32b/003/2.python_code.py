
def policy(piles: list[int]) -> str:
    # Check if all piles have exactly 1 object
    all_ones = all(p == 1 for p in piles)
    if all_ones:
        # If even number of 1s, take one from first pile (winning move)
        return "0,1"
    
    # Compute nim-sum (XOR) of all piles
    xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    if xor_sum != 0:
        # Find a move to make the new XOR zero
        for pile in range(4):
            if piles[pile] > 0:
                desired = piles[pile] ^ xor_sum
                if desired < piles[pile]:
                    take = piles[pile] - desired
                    return f"{pile},{take}"
    else:
        # XOR is zero and not all ones: make any valid move
        for pile in range(4):
            if piles[pile] > 0:
                return f"{pile},1"
    
    # Fallback: always return a valid move
    for pile in range(4):
        if piles[pile] > 0:
            return f"{pile},1"
