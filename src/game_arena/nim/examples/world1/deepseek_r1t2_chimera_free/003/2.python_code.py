
def policy(piles: list[int]) -> str:
    # Check if all non-zero piles are exactly 1
    remaining = [p for p in piles if p > 0]
    if all(p == 1 for p in remaining):
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Count big piles (size >1)
    big_piles = [i for i, p in enumerate(piles) if p > 1]
    if len(big_piles) == 1:
        i = big_piles[0]
        x = piles[i]
        c = sum(1 for p in piles if p == 1)  # Number of ones
        # Choose take amount based on parity of c
        take = x - 1 if c % 2 == 0 else x
        take = max(1, min(take, piles[i]))  # Ensure legal move
        return f"{i},{take}"
    
    # Calculate nim-sum and find optimal move
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    if nim_sum != 0:
        # Find moves that zero nim_sum without leaving all ones
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                new_piles = piles.copy()
                new_piles[i] = target
                # Check if new state has any pile >1
                if any(p > 1 for p in new_piles):
                    return f"{i},{take}"
        # Fallback: zero nim_sum even if leaves all ones
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # Default: take 1 from largest pile
    max_idx = -1
    max_val = -1
    for i in range(4):
        if piles[i] > max_val:
            max_val = piles[i]
            max_idx = i
    return f"{max_idx},1" if max_idx != -1 else f"{next(i for i, p in enumerate(piles) if p > 0)},1"
