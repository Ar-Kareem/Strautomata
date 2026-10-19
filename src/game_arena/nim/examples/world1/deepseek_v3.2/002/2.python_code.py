
import sys

def policy(piles: list[int]) -> str:
    # Misère Nim for 4 piles
    n = len(piles)

    # Step 1: Compute Nim-sum
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    # Helper: Count piles with size > 1
    def count_gt1(ps):
        return sum(1 for x in ps if x > 1)

    # Helper: Count piles with size == 1
    def count_eq1(ps):
        return sum(1 for x in ps if x == 1)

    # Step 2: Try normal winning move if xor_sum != 0
    if xor_sum != 0:
        for i in range(n):
            if piles[i] == 0:
                continue
            target_size = piles[i] ^ xor_sum
            if target_size < piles[i]:
                take_amount = piles[i] - target_size
                # Check if this move leaves all piles <= 1
                new_piles = piles.copy()
                new_piles[i] = target_size
                if count_gt1(new_piles) == 0:
                    # All piles are 0 or 1 now
                    ones = count_eq1(new_piles)
                    # In misère, facing odd number of 1's is losing for the *next* player
                    # So if 'ones' is odd, this move is good (opponent loses)
                    # If 'ones' is even, maybe adjust
                    if ones % 2 == 1:
                        # Winning move
                        return f"{i},{take_amount}"
                    else:
                        # Try to leave an extra object somewhere else if possible
                        # Look for another pile >1 to adjust
                        for j in range(n):
                            if piles[j] > 1 and j != i:
                                # Instead take from pile j to leave odd ones
                                # Try making pile j = 0 or 1
                                for take in range(1, piles[j] + 1):
                                    test_piles = piles.copy()
                                    test_piles[j] -= take
                                    if count_gt1(test_piles) == 0:
                                        test_ones = count_eq1(test_piles)
                                        if test_ones % 2 == 1:
                                            return f"{j},{take}"
                else:
                    # Normal winning move
                    return f"{i},{take_amount}"

    # Step 3: If xor_sum == 0 or no normal winning move found
    # Try to force opponent into odd number of 1's
    for i in range(n):
        if piles[i] == 0:
            continue
        # Try taking all from pile i if possible
        if piles[i] > 0:
            new_piles = piles.copy()
            new_piles[i] = 0
            if count_gt1(new_piles) == 0:
                ones = count_eq1(new_piles)
                if ones % 2 == 1:
                    return f"{i},{piles[i]}"
        # Try leaving 1 in pile i
        if piles[i] > 1:
            new_piles = piles.copy()
            new_piles[i] = 1
            if count_gt1(new_piles) == 0:
                ones = count_eq1(new_piles)
                if ones % 2 == 1:
                    take_amt = piles[i] - 1
                    return f"{i},{take_amt}"
        # Try other amounts
        for take in range(1, piles[i] + 1):
            new_piles = piles.copy()
            new_piles[i] -= take
            if count_gt1(new_piles) == 0:
                ones = count_eq1(new_piles)
                if ones % 2 == 1:
                    return f"{i},{take}"

    # Step 4: Fallback — remove 1 from largest pile
    max_pile_idx = max(range(n), key=lambda i: piles[i])
    return f"{max_pile_idx},1"
