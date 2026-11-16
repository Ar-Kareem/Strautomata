
def policy(piles):
    xor_total = 0
    for p in piles:
        xor_total ^= p
    
    all_ones = all(p == 1 for p in piles)
    
    if xor_total != 0:
        for i in range(4):
            target = piles[i] ^ xor_total
            if target < piles[i] and target != 0:
                return f"{i},{piles[i] - target}"
            elif target < piles[i]:
                if all([p == 0 for p in piles] and p != piles[i]):
                    continue
                return f"{i},{piles[i] - target}"
            if target < piles[i]:
                return f"{i},{piles[i] - target}"
    else:
        if all_ones:
            return "0,1"
        else:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    return "0,1"
