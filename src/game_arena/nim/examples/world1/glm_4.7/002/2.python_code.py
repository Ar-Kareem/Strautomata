
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Helper function to determine if a state is "winning for the player about to move"
    # In Misère Nim, a state of "all ones with even count" is Winning for the receiver.
    # A state of "all ones with odd count" is Losing for the receiver.
    def is_state_winning_for_receiver(state_piles):
        if max(state_piles) <= 1:
            # We are in the endgame (all piles are 0 or 1)
            count_ones = sum(1 for x in state_piles if x > 0)
            # Even count of 1s -> Winning for player to move
            # Odd count of 1s -> Losing for player to move
            return count_ones % 2 == 0
        # If not endgame, standard Nim logic applies: nim_sum == 0 is Losing for receiver.
        # However, we use this helper primarily to detect the specific Misère trap.
        # For mixed piles, "winning for receiver" is determined by nim_sum == 0.
        # But this helper is specifically checking the "bad" endgame condition.
        return False

    # Helper to find index of largest pile
    def get_largest_pile_idx(current_piles):
        max_val = -1
        idx = -1
        for i, p in enumerate(current_piles):
            if p > max_val:
                max_val = p
                idx = i
        return idx

    # CASE 1: Nim-sum is 0
    # In standard Nim, this is a losing position. We just want to make a valid move,
    # preferably taking 1 from the largest pile to delay the end.
    # Note: In "all ones" endgame, nim_sum == 0 implies Even count (Winning position).
    # Taking 1 from a pile converts Even to Odd, which is the correct winning move.
    # So "take 1" works for both the Losing (mixed) and Winning (all-ones) cases when nim_sum == 0.
    if nim_sum == 0:
        idx = get_largest_pile_idx(piles)
        return f"{idx},1"

    # CASE 2: Nim-sum is not 0
    # We are in a winning position. We try to make a move that makes nim_sum 0.
    # However, we must avoid moving to a state where the receiver wins (Bad Endgame).
    
    # Try standard winning moves (nim_sum -> 0)
    for i in range(4):
        if piles[i] > 0:
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                new_piles = list(piles)
                new_piles[i] = target
                
                # If this resulting state is NOT winning for the receiver, it's a safe move.
                if not is_state_winning_for_receiver(new_piles):
                    return f"{i},{take}"
                
                # If it IS winning for receiver (i.e., we left even count of 1s),
                # we skip this move and look for another one.

    # CASE 3: All standard winning moves lead to the bad endgame (even count of 1s).
    # This implies we are in a specific winning configuration where we must force
    # the "good" endgame (odd count of 1s) manually.
    
    # First, check if we are already in the endgame (all piles <= 1).
    # If nim_sum != 0 and max <= 1, we have Odd count (Losing for us).
    # Any move leads to Even count (Winning for opponent).
    # We just make a move (take 1).
    if max(piles) <= 1:
        idx = get_largest_pile_idx(piles)
        return f"{idx},1"

    # We are in mixed piles (Winning). We need to force endgame with Odd ones.
    # We iterate piles to find a reduction that leaves max <= 1 and odd count.
    for i in range(4):
        if piles[i] > 1:
            # Try reducing this pile to 1
            take_to_one = piles[i] - 1
            temp_piles = list(piles)
            temp_piles[i] = 1
            if not is_state_winning_for_receiver(temp_piles):
                return f"{i},{take_to_one}"
            
            # Try reducing this pile to 0
            take_all = piles[i]
            temp_piles = list(piles)
            temp_piles[i] = 0
            if not is_state_winning_for_receiver(temp_piles):
                return f"{i},{take_all}"

    # Ultimate fallback (should theoretically not be reached with correct logic)
    idx = get_largest_pile_idx(piles)
    return f"{idx},1"
