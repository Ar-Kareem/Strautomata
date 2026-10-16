
def policy(piles):
    # All piles are 0 or 1
    if all(p <= 1 for p in piles):
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # fallback (should never be needed)
        return "0,0"

    # Compute nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Losing position under normal play; make any legal move
    if nim_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"

    # Find a winning move
    for i, p in enumerate(piles):
        key = p ^ nim_sum
        if key < p:
            take = p - key
            new_piles = piles.copy()
            new_piles[i] = key
            # If move leaves only 0s and 1s, ensure odd number of 1s
            if all(x <= 1 for x in new_piles):
                if sum(new_piles) % 2 == 0:
                    if key == 1:
                        take += 1  # leave 0 instead of 1
                    elif key == 0:
                        take -= 1  # leave 1 instead of 0
            return f"{i},{take}"

    # Fallback (should not be reached)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    return "0,0"
