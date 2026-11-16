
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum != 0:
        for i in range(4):
            target = nim_sum ^ piles[i]
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    else:
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
