
import sys

def policy(piles: list[int]) -> str:
    if len(piles) != 4:
        return "0,1"  # fallback in case of unexpected input
    
    # Check if all piles are 1 (or zero, with some 1's)
    all_ones = True
    for pile in piles:
        if pile > 1:
            all_ones = False
            break
    total_objects = sum(piles)
    
    if all_ones:
        # In misère Nim, leave odd number of 1's for opponent. So if total number is even, take all from one pile.
        if total_objects % 2 == 1:
            # If total is odd, need to take 1 to make even
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        else:
            # Take a whole pile (e.g., 1)
            for i in range(4):
                if piles[i] >= 1:
                    return f"{i},{piles[i]}"
    
    # Standard Nim strategy applying XOR sum
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    if xor_sum != 0:
        # Find a pile where XOR sum with current pile is less than current pile
        for i in range(4):
            if piles[i] ^ xor_sum < piles[i]:
                take = piles[i] - (piles[i] ^ xor_sum)
                if take >= 1 and take <= piles[i]:
                    return f"{i},{take}"
    else:
        # No winning move possible, take one from the largest pile to prolong the game
        max_pile = max(piles)
        if max_pile == 0:
            return "0,1"  # shouldn't happen as piles may not be empty on our turn
        for i in range(4):
            if piles[i] == max_pile:
                return f"{i},1"
    
    # Fallback: take one from the first non-zero pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    return "0,1"
