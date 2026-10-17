
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    large_count = sum(1 for p in piles if p > 1)
    ones = sum(1 for p in piles if p == 1)
    
    if large_count == 0:
        # Endgame: all piles are 0 or 1
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
    
    elif large_count == 1:
        # Exactly one pile > 1: control the endgame
        for i, p in enumerate(piles):
            if p > 1:
                # Leave opponent with odd number of 1-piles
                if ones % 2 == 0:
                    take = p - 1  # Reduce to 1, making total ones odd
                else:
                    take = p  # Reduce to 0, keeping total ones odd
                return f"{i},{take}"
    
    else:  # large_count >= 2
        if nim_sum == 0:
            # Losing position, make any legal move
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
        else:
            # Winning position, standard Nim move to make nim_sum = 0
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    return f"{i},{p - target}"
    
    # Fallback (shouldn't reach in valid game state)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    return "0,1"
