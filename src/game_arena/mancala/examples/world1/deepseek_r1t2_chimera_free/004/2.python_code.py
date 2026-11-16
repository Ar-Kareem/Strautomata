
import math

def simulate_move(current, other, move_index):
    """Simulate a move for the current player and return the new state."""
    new_curr = current.copy()
    new_other = other.copy()
    
    seeds = new_curr[move_index]
    if seeds == 0:
        return current, other, False  # Illegal move
    
    new_curr[move_index] = 0
    current_pos = move_index + 1
    current_side = 'current'
    last_side = None
    last_pos = None
    
    for _ in range(seeds):
        if current_side == 'current':
            if current_pos < 6:
                new_curr[current_pos] += 1
                last_side = 'current'
                last_pos = current_pos
                current_pos += 1
            elif current_pos == 6:  # Store
                new_curr[6] += 1
                last_side = 'current'
                last_pos = 6
                current_side = 'other'
                current_pos = 0
            else:  # Wrap to other side
                current_side = 'other'
                current_pos = 0
        else:  # Other side
            if current_pos < 6:
                new_other[current_pos] += 1
                last_side = 'other'
                last_pos = current_pos
                current_pos += 1
            elif current_pos == 6:  # Skip opponent's store
                current_side = 'current'
                current_pos = 0
            else:  # Wrap to current side
                current_side = 'current'
                current_pos = 0
        
        # Handle position wraparound
        if current_side == 'current' and current_pos > 6:
            current_pos = 0
        elif current_side == 'other' and current_pos > 6:
            current_pos = 0
    
    # Check for extra move
    extra = (last_side == 'current' and last_pos == 6)
    
    # Check for capture
    if last_side == 'current' and last_pos is not None and 0 <= last_pos < 6:
        if new_curr[last_pos] == 1:  # Was empty before
            opp_index = 5 - last_pos
            if new_other[opp_index] > 0:
                new_curr[6] += new_curr[last_pos] + new_other[opp_index]
                new_curr[last_pos] = 0
                new_other[opp_index] = 0
    
    # Check if game ended
    if sum(new_curr[:6]) == 0 or sum(new_other[:6]) == 0:
        new_curr[6] += sum(new_curr[:6])
        new_other[6] += sum(new_other[:6])
        for i in range(6):
            new_curr[i] = 0
            new_other[i] = 0
    
    return new_curr, new_other, extra

def evaluate(you, opponent):
    """Evaluate the state's favorability for the current player (you)."""
    store_diff = you[6] - opponent[6]
    house_diff = sum(you[:6]) - sum(opponent[:6])
    # Bonus for possible captures in the next move
    capture_potential = sum(
        other_seeds if you[i] == 0 and house_idx != i else 0
        for i, (you_seeds, house_idx) in enumerate(zip(you[:6], range(5, -1, -1)))
        for other_seeds in [opponent[house_idx]]
    )
    return store_diff * 2 + house_diff * 0.5 + capture_potential * 0.8

def policy(you, opponent):
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_value = -math.inf
    best_move = legal_moves[0]
    
    for move in legal_moves:
        # Simulate our move
        new_you, new_opp, extra = simulate_move(you, opponent, move)
        if extra:
            # Second move opportunity - take the best possible immediate move
            second_move_val = -math.inf
            second_legal = [i for i in range(6) if new_you[i] > 0]
            for second_move in second_legal:
                final_you, final_opp, _ = simulate_move(new_you, new_opp, second_move)
                val = evaluate(final_you, final_opp)
                if val > second_move_val:
                    second_move_val = val
            current_val = second_move_val
        else:
            # Simulate opponent's best response
            min_val = math.inf
            opp_legal = [i for i in range(6) if new_opp[i] > 0]
            for opp_move in opp_legal:
                opp_you, opp_you_opp, opp_extra = simulate_move(new_opp, new_you, opp_move)
                if opp_extra:
                    # Opponent gets another move - evaluate their best follow-up
                    opp_second_val = -math.inf
                    opp_second_legal = [i for i in range(6) if opp_you[i] > 0]
                    for opp_second in opp_second_legal:
                        final_opp_you, final_opp_opp, _ = simulate_move(opp_you, opp_you_opp, opp_second)
                        opp_val = evaluate(final_opp_opp, final_opp_you)  # Swap perspective
                        if opp_val > opp_second_val:
                            opp_second_val = opp_val
                    val = opp_second_val
                else:
                    val = evaluate(opp_you_opp, opp_you)  # Swap perspective
                if val < min_val:
                    min_val = val
            current_val = min_val
        
        # Update best move
        if current_val > best_value or (current_val == best_value and you[move] > you[best_move]):
            best_value = current_val
            best_move = move
            
    return best_move
