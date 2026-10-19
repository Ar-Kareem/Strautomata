
def policy(piles: list[int]) -> str:
    if all(p == 1 for p in piles):
        return "0,1"  # Winning move when all piles are 1
    
    xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    if xor_sum != 0:
        # Find a pile to make the new XOR sum zero
        for i in range(4):
            current = piles[i]
            target = current ^ xor_sum
            if target < current:
                take = current - target
                return f"{i},{take}"
        # Fallback (should not reach here if logic is correct)
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Nim sum is zero, force a non-optimal configuration for opponent
        for i in range(4):
            if piles[i] > 1:
                return f"{i},1"
        # Fallback (should not reach here)
        return "0,1"
