
def policy(piles):
    # If all piles are 0 or 1
    if max(piles) == 1:
        # We have to take one object from a pile that has exactly 1
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
        # This should not happen since max=1 and not all zero (because game would be over)
        # But if all zero, the game is over, so we assume at least one non-zero.
        return "0,1"  # fallback

    # Compute XOR (nim-sum) of all piles
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    # Check for a move that is the normal Nim move and that avoids endgame (leaves at least one heap >1)
    for i in range(4):
        if piles[i] == 0:
            continue
        target = xor_sum ^ piles[i]
        if target < piles[i]:
            # Check how many heaps will be >1 after the move
            count_gt1 = 0
            for j in range(4):
                val = piles[j] if j != i else target
                if val > 1:
                    count_gt1 += 1
            if count_gt1 > 0:
                # This move leaves at least one heap > 1, so we can play normally
                return f"{i},{piles[i] - target}"

    # If we are here, then every normal move (that makes nim-sum=0) leaves only 0s and 1s.
    # So we try to find a move that leaves an odd number of 1s
    best_move = None
    for i in range(4):
        if piles[i] == 0:
            continue
        # Count the number of ones in the other piles
        current_ones = 0
        for j in range(4):
            if j != i:
                if piles[j] == 1:
                    current_ones += 1
        # Option 1: reduce pile i to 0 -> total ones = current_ones
        if current_ones % 2 == 1:
            # Then reducing pile i to 0 leaves odd ones -> good
            return f"{i},{piles[i]}"
        # Option 2: reduce pile i to 1 -> total ones = current_ones + 1
        elif (current_ones + 1) % 2 == 1:
            # This is when current_ones is even, then we want to reduce to 1 to make it odd
            # We can do it only if piles[i] >= 2
            if piles[i] >= 2:
                return f"{i},{piles[i]-1}"

    # If none of the above, then we must have a pile > 1 and not been captured.
    # This should not happen because the game is winning, there must be a move.
    # Fallback: reduce the largest pile by 1
    max_val = 0
    max_index = 0
    for i in range(4):
        if piles[i] > max_val:
            max_val = piles[i]
            max_index = i
    return f"{max_index},1"
