
def policy(you, opponent):
    max_eval = -float('inf')
    best_move = 0
    for move in range(6):
        if you[move] == 0:
            continue
        
        # Create copies of the current state
        new_you = you.copy()
        new_opp = opponent.copy()
        seeds = new_you[move]
        new_you[move] = 0
        pos = move + 1
        remaining = seeds
        last_house = None
        
        while remaining > 0:
            if pos == 6:  # Your store
                new_you[pos] += remaining
                remaining = 0
                last_house = 6
            elif pos < len(new_you):
                # Your own house
                new_you[pos] += 1
                remaining -= 1
                last_house = pos if remaining == 0 else last_house
            else:
                # Opponent's houses (virtual positions 7-12)
                sim_op_pos = pos - 7
                new_opp[sim_op_pos] += 1
                if remaining == 0:
                    last_house = None  # Not your house, so no capture possible
                remaining -= 1
            pos += 1
        
        # Check for captures
        if last_house is not None and last_house < 6:
            if you[last_house] == 0:  # Check if house was empty before this move
                opp_house = 5 - last_house
                captured = new_opp[opp_house]
                new_you[6] += 1 + captured
                new_you[last_house] = 0
                new_opp[opp_house] = 0
        
        # Evaluate the resulting state
        eval_val = new_you[6] - new_opp[6]
        evaluator2 = sum(new_you[:6]) - sum(new_opp[:6])
        current_eval = eval_val + evaluator2
        
        if current_eval > max_eval:
            max_eval = current_eval
            best_move = move
    
    return best_move
