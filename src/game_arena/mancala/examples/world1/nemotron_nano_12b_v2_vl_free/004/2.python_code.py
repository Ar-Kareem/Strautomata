
def policy(you, opponent):
    possible_moves = [i for i in range(6) if you[i] > 0]
    if not possible_moves:
        return 0  # As per problem statement, this should not occur
    
    best_move = possible_moves[0]
    best_capture_score = -1
    best_extra_move_score = 0
    
    for move in possible_moves:
        new_you = list(you)
        new_opp = list(opponent)
        seeds = new_you[move]
        new_you[move] = 0
        current_pos = move + 1
        seeds_placed = 0
        last_pos = None
        
        while seeds_placed < seeds:
            if current_pos == 6:
                new_you[6] += 1
                last_pos = current_pos
            elif current_pos < 6:
                new_you[current_pos] += 1
                last_pos = current_pos
            else:
                new_opp[current_pos - 6] += 1
                last_pos = current_pos
            current_pos = (current_pos + 1) % 12
            seeds_placed += 1
        
        capture = 0
        if last_pos < 6:
            if new_you[last_pos] == 1:
                opp_pos = 5 - last_pos
                if new_opp[opp_pos] > 0:
                    capture = new_opp[opp_pos]
                    new_you[6] += capture
                    new_opp[opp_pos] = 0
        
        end_in_store = (last_pos == 6)
        move_score = capture * 1000 + (1 if end_in_store else 0)
        
        if (move_score > best_capture_score) or (move_score == best_capture_score and (end_in_store > best_has_extra)):
            best_capture_score = move_score
            best_has_extra = 1 if end_in_store else 0
            best_move = move
    
    return best_move
