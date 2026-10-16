
def policy(piles):
    # Check if all non-zero piles are of size 1
    non_zero = [x for x in piles if x > 0]
    if all(x == 1 for x in non_zero):
        # All non-zero are 1 -> use all-ones strategy
        n = len(non_zero)
        if n % 2 == 0:
            # Remove one entire heap (choose the first non-zero pile)
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},{piles[i]}"
        else:
            # Remove one entire heap arbitrarily
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},{piles[i]}"
    else:
        # Not all ones
        s = 0
        for i in range(4):
            s ^= piles[i]
        if s != 0:
            # Use normal Nim strategy to leave nim_sum=0
            for i in range(4):
                if piles[i] == 0:
                    continue
                y = piles[i] ^ s
                if y < piles[i]:
                    take_amount = piles[i] - y
                    return f"{i},{take_amount}"
        else:
            # s==0 -> P-position, we are in a losing position, try to make it hard for opponent
            count_ones = sum(1 for x in piles if x == 1)
            # Try reducing a heap>1 to 1 to get an odd count of ones
            if (count_ones + 1) % 2 == 1:
                for i in range(4):
                    if piles[i] > 1:
                        take_amount = piles[i] - 1
                        return f"{i},{take_amount}"
            # If that doesn't work, try removing an entire heap to get odd count of ones
            if count_ones % 2 == 1:
                for i in range(4):
                    if piles[i] > 1:
                        return f"{i},{piles[i]}"
            # Fallback: remove an entire heap arbitrarily
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},{piles[i]}"
