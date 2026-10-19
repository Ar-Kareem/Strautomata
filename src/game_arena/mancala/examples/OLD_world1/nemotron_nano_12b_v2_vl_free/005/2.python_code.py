
def policy(you, opponent):
    possible_moves = [i for i in range(6) if you[i] > 0]
    if not possible_moves:
        return 0  # This case should not occur as per problem statement
    
    best_move = None
    best_priority_score = (float('inf'), False, float('inf'), 0)  # (captured_score, ends_store, i)
    
    for i in possible_moves:
        s = you[i]
        # Generate the distribution order
        cycle = list(range(i+1, 6)) + [6]  # your houses i+1..5, then store
        cycle += list(range(6))             # opponents 0..5
        cycle += list(range(6))             # your own 0..5
        cycle_len = len(cycle)
        
        # Find the last position in cycle
        last_pos = cycle[(s - 1) % cycle_len]
        
        captured = False
        captured_seeds = 0
        ends_store = (last_pos == 6)
        is_promising = False
        
        if last_pos in range(6):  # your house
            if you[last_pos] == 0:  # if originally empty
                opponent_p = 5 - last_pos
                if opponent[opponent_p] > 0:
                    cap_seed = 1 + opponent[opponent_p]
                    move_data = (-cap_seed, 0 if ends_store else 1, 0, i)
                    is_promising = True
                    captured_seeds = cap_seed
                else:
                    captured_seeds = 0
        else:
            captured_seeds = 0
        
        # Check for store move (extra turn)
        ends_store = (last_pos == 6)
        if ends_store:
            capital_p = (-captured_seeds, 0, 1, i)
            is_promising = False
        else:
            capital_p = (-captured_seeds, 0 if ends_store else 1, 1, i)
            is_promising = False
        
        # Determine if this move should be prioritized
        if is_promising or (not any_end_store and is_promising):
            pass
        
        current_priority = (-captured_seeds, 0 if ends_store else 1, i)
        if priority_tuple < best_priority_score:
            best_priority_score = priority_tuple
            best_move = i
    
    return best_move
