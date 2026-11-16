
def policy(piles: list[int]) -> str:
    # Check if all piles are 0 or 1
    if all(p <= 1 for p in piles):
        ones_count = sum(piles)
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    else:
        # Compute Nim-sum
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
            
        if nim_sum != 0:
            # Look for a move avoiding all-ones even and zero-sum
            for i in range(4):
                if piles[i] == 0:
                    continue
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    new_piles = piles.copy()
                    new_piles[i] = target
                    # Skip if move ends the game (losing)
                    if sum(new_piles) == 0:
                        continue
                    # Skip if move leaves all-ones and even count
                    if all(p <= 1 for p in new_piles):
                        ones_cnt = sum(new_piles)
                        if ones_cnt % 2 == 0:
                            continue
                    return f"{i},{take}"
            
            # Fallback: take 1 from largest pile (ensuring not to lose)
            max_val = max(piles)
            for i in range(4):
                if piles[i] == max_val:
                    new_piles = piles.copy()
                    new_piles[i] -= 1
                    if sum(new_piles) == 0:
                        continue
                    return f"{i},1"
            # If forced to lose (e.g., [1,0,0,0]), take last object
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Nim-sum zero: take 1 from largest pile
            max_val = max(piles)
            for i in range(4):
                if piles[i] == max_val:
                    new_piles = piles.copy()
                    new_piles[i] -= 1
                    if sum(new_piles) == 0:
                        continue
                    return f"{i},1"
            # If forced to lose
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
