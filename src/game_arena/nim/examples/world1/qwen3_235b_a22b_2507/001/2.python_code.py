
def policy(piles: list[int]) -> str:
    # Count the number of piles with more than 1 object
    big = 0
    for x in piles:
        if x > 1:
            big += 1

    # Case 1: no pile has more than 1
    if big == 0:
        # All non-zero piles are of size 1. Take one from the first non-empty pile.
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Case 2: exactly one pile has more than 1
    elif big == 1:
        big_index = -1
        ones = 0
        for i in range(4):
            if piles[i] > 1:
                big_index = i
            elif piles[i] == 1:
                ones += 1
        # Adjust the big pile to control the parity of 1s
        if ones % 2 == 1:
            # Leave an odd number of 1s by removing the entire big pile
            take = piles[big_index]
        else:
            # Leave an odd number of 1s by reducing the big pile to 1
            take = piles[big_index] - 1
        return f"{big_index},{take}"
    
    # Case 3: two or more piles have more than 1
    else:
        # Compute XOR of all pile sizes
        xor_all = 0
        for x in piles:
            xor_all ^= x
        
        if xor_all != 0:
            # Normal Nim move: make XOR zero
            for i in range(4):
                desired = xor_all ^ piles[i]
                if desired < piles[i]:
                    take = piles[i] - desired
                    return f"{i},{take}"
        # If we reach here, either xor_all==0 or no move found (should not happen in first)
        # In a losing position (xor_all==0) or fallback: reduce the first pile with more than 1 by one
        for i in range(4):
            if piles[i] > 1:
                return f"{i},1"
        # Fallback: if no pile has more than 1 (should not happen), take one from first non-empty
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
