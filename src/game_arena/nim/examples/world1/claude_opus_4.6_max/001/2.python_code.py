
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    big = [i for i in range(4) if piles[i] >= 2]
    ones = sum(1 for p in piles if p == 1)
    
    if not big:
        # All piles are 0 or 1: take from any 1-pile
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
        return "0,1"  # fallback
    
    if len(big) == 1:
        # Exactly one pile >= 2: always winning in misere Nim
        i = big[0]
        if ones % 2 == 0:
            # Leave pile as 1 -> total ones becomes odd (P-position for opponent)
            return f"{i},{piles[i] - 1}"
        else:
            # Leave pile as 0 -> total ones stays odd (P-position for opponent)
            return f"{i},{piles[i]}"
    
    # Multiple piles >= 2
    if nim_sum != 0:
        # Winning position: standard Nim XOR strategy to make nim-sum 0
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                return f"{i},{piles[i] - target}"
    
    # Losing position (nim_sum == 0 with multiple big piles):
    # take 1 from the largest pile as heuristic
    best = max(range(4), key=lambda i: piles[i])
    return f"{best},1"
