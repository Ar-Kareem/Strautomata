
import random

def policy(piles: list[int]) -> str:
    # Compute Nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Helper: count of piles with size 1
    def count_ones(state):
        return sum(1 for x in state if x == 1)

    # Helper: check if all piles are size 0 or 1
    def all_at_most_one(state):
        return all(x <= 1 for x in state)

    # If Nim-sum != 0 (winning position in normal Nim)
    if nim_sum != 0:
        best_move = None
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                # Simulate move
                new_piles = piles.copy()
                new_piles[i] -= take
                # Check if move leaves all piles <= 1
                if all_at_most_one(new_piles):
                    ones = count_ones(new_piles)
                    if ones % 2 == 1:  # opponent gets odd ones -> losing for them
                        return f"{i},{take}"
                    else:
                        # This move leaves even ones -> winning for opponent, avoid if possible
                        continue
                else:
                    return f"{i},{take}"
        # If all winning moves lead to even ones and all <=1, just pick first winning move
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    else:
        # Nim-sum = 0: losing in normal play, in misère try to force all 1s & even count
        # If already all <=1
        if all_at_most_one(piles):
            # Take 1 from first non-zero pile
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
        # Else try to move to all piles <=1 with even count of 1s
        for i in range(4):
            if piles[i] > 1:
                # Try taking piles[i] - 1 (leave 1)
                take = piles[i] - 1
                new_piles = piles.copy()
                new_piles[i] = 1
                if all_at_most_one(new_piles):
                    ones = count_ones(new_piles)
                    if ones % 2 == 0:  # opponent gets even ones -> losing for them
                        return f"{i},{take}"
        # If not possible, take 1 from largest pile (delay)
        max_pile = max(piles)
        for i in range(4):
            if piles[i] == max_pile and piles[i] > 0:
                return f"{i},1"
    # Fallback (should not happen)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"
