
def policy(piles: list[int]) -> str:
    """
    Optimally solve Misere Nim for 4 piles.
    Strategy:
    1. If all piles are 0 or 1: Play based on parity (odd sum -> remove all/leftover, even sum -> remove 1).
    2. If at least one pile > 1: Play standard Nim (XOR sum) strategy, but avoid moves that leave 
       all non-zero piles as 1s (which is a losing position for the opponent in standard play 
       but a winning position for them in misere play if the sum is odd).
    """
    # Helper to calculate XOR sum
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    # Case 1: All piles are 0 or 1
    if all(p <= 1 for p in piles):
        # Count number of 1s
        count_ones = sum(piles)
        # If odd (1, 3), remove one to leave even (0, 2) for opponent
        # If even (0, 2, 4), remove one to leave odd (1, 3) for opponent
        # Actually, we want to leave an even number of 1s for the opponent.
        # If sum is odd, removing 1 makes it even (winning).
        # If sum is even, removing 1 makes it odd (losing if opponent plays optimally).
        take = 1
        # Find a pile with a 1
        pile_idx = -1
        for i in range(4):
            if piles[i] == 1:
                pile_idx = i
                break
        # If no pile with 1 (all 0), game is over, but code shouldn't reach here.
        return f"{pile_idx},{take}"

    # Case 2: At least one pile > 1
    # Standard Nim strategy: make Nim-sum 0, unless it creates the "all ones" trap.
    
    best_move = None
    
    for i in range(4):
        # Calculate target size for pile i to make XOR sum 0
        # target = piles[i] ^ xor_sum
        # We need to reduce piles[i] to target, so we need piles[i] > target
        target = piles[i] ^ xor_sum
        if target < piles[i]:
            take_amount = piles[i] - target
            
            # Check for the "All ones" trap in the resulting state
            # Create temporary state
            temp_piles = piles[:]
            temp_piles[i] = target
            
            # Check if all non-zero piles in temp_piles are 1
            non_zero_piles = [p for p in temp_piles if p > 0]
            is_all_ones = all(p == 1 for p in non_zero_piles)
            
            if is_all_ones:
                # This move leads to a state like [1, 1, 0, 0] or [1, 1, 1, 0].
                # In misere, if sum of ones is ODD, it's a winning position for the player to move.
                # If sum is EVEN, it's losing.
                # We want to leave the opponent a losing position.
                # So we should AVOID leaving an ODD sum of ones.
                if sum(non_zero_piles) % 2 != 0:
                    # This move is bad (leaves opponent with odd sum, e.g., 1 or 3 ones).
                    continue
            
            # If we reach here, the move is valid and optimal (or best found so far)
            best_move = (i, take_amount)
            break # Found a valid Nim-move, take it

    # If no valid Nim-move found (e.g., all Nim moves lead to odd 'all ones' state),
    # fallback strategy: remove 1 from the largest pile.
    if best_move is None:
        # Find largest pile
        max_val = -1
        max_idx = -1
        for i in range(4):
            if piles[i] > max_val:
                max_val = piles[i]
                max_idx = i
        best_move = (max_idx, 1)

    return f"{best_move[0]},{best_move[1]}"
