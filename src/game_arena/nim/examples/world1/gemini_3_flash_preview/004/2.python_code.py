
def policy(piles: list[int]) -> str:
    # Calculate the current Nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Determine the move based on the Nim-sum (Normal Play Strategy)
    target_move = None
    if nim_sum != 0:
        for i, p in enumerate(piles):
            # If (current pile size XOR nim_sum) < current pile size,
            # we can reduce the pile to that value to make the total XOR sum 0.
            target_size = p ^ nim_sum
            if target_size < p:
                # Check Misere condition:
                # If this move leaves only piles of size 1, we must leave an odd number of them.
                remaining_piles = [piles[j] if i != j else target_size for j in range(len(piles))]
                if all(val <= 1 for val in remaining_piles):
                    # To leave an odd number of 1s, count how many 1s are in other piles
                    others_count_one = sum(1 for j, val in enumerate(piles) if i != j and val == 1)
                    # If others_count_one is even, we make this pile 1. If odd, we make it 0.
                    final_val = 1 if others_count_one % 2 == 0 else 0
                    target_move = (i, p - final_val)
                else:
                    target_move = (i, p - target_size)
                break

    # If already in a losing position (nim_sum == 0) or no move found, 
    # make the smallest legal move possible.
    if target_move is None:
        for i, p in enumerate(piles):
            if p > 0:
                target_move = (i, 1)
                break
                
    return f"{target_move[0]},{target_move[1]}"
