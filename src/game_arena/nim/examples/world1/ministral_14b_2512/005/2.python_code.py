
def policy(piles: list[int]) -> str:
    # Calculate the nim-sum (XOR) of all piles
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If nim-sum is non-zero, make a move to leave nim-sum zero (standard Nim strategy)
    if nim_sum != 0:
        for i in range(4):
            if piles[i] != 0:
                # Calculate the target nim-sum after removing 'take' objects from pile i
                target = nim_sum ^ piles[i]
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"

    # If nim-sum is zero, we need to handle the misère case
    # Count the number of non-zero piles
    non_zero_piles = [p for p in piles if p != 0]
    num_non_zero = len(non_zero_piles)

    # Case 1: All piles are non-zero (equivalent to standard Nim)
    if num_non_zero == 4:
        # This should not happen because nim_sum would be non-zero if all piles are non-zero
        # and we would have returned a move above. Fallback to standard Nim move.
        for i in range(4):
            if piles[i] != 0:
                return f"{i},1"

    # Case 2: One pile is zero (3-pile misère Nim)
    elif num_non_zero == 3:
        # Find the largest pile
        largest_pile = max(non_zero_piles)
        largest_index = piles.index(largest_pile)

        # If the largest pile is not the only pile, reduce it to match the XOR of the other two
        if len(non_zero_piles) > 1:
            other_piles = [p for p in non_zero_piles if p != largest_pile]
            xor_other = other_piles[0] ^ other_piles[1]
            if xor_other < largest_pile:
                take = largest_pile - xor_other
                return f"{largest_index},{take}"

        # If all piles are equal, take all but one from the largest pile
        if all(p == largest_pile for p in non_zero_piles):
            return f"{largest_index},{largest_pile - 1}"

        # Fallback: take all but one from the largest pile
        return f"{largest_index},{largest_pile - 1}"

    # Case 3: Two piles are zero (2-pile misère Nim)
    elif num_non_zero == 2:
        # In 2-pile misère Nim, the losing position is when both piles are equal.
        # So, if the piles are equal, we must take all from one pile.
        if non_zero_piles[0] == non_zero_piles[1]:
            return f"{piles.index(non_zero_piles[0])},{non_zero_piles[0]}"
        else:
            # Otherwise, make the piles equal by taking from the larger pile
            larger_index = piles.index(max(non_zero_piles))
            larger_pile = max(non_zero_piles)
            smaller_pile = min(non_zero_piles)
            take = larger_pile - smaller_pile
            return f"{larger_index},{take}"

    # Case 4: Three piles are zero (1-pile misère Nim)
    elif num_non_zero == 1:
        # The only move is to take all objects (since the player to move loses)
        return f"{piles.index(non_zero_piles[0])},{non_zero_piles[0]}"

    # Fallback: take 1 from the first non-zero pile (should not happen in correct play)
    for i in range(4):
        if piles[i] != 0:
            return f"{i},1"
