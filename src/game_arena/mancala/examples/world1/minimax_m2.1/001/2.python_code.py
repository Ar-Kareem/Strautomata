
import math

def eval_state(my_state, opponent_state):
    # Check if game over
    my_houses_sum = sum(my_state[:6])
    opp_houses_sum = sum(opponent_state[:6])
    if my_houses_sum == 0 or opp_houses_sum == 0:
        # Game over: collect remaining seeds
        my_final = my_state[6] + my_houses_sum
        opp_final = opponent_state[6] + opp_houses_sum
        if my_final > opp_final:
            return 10000  # Win
        elif my_final < opp_final:
            return -10000  # Loss
        else:
            return 0  # Draw
    
    # Heuristic evaluation
    store_diff = my_state[6] - opponent_state[6]
    houses_diff = my_houses_sum - opp_houses_sum
    # Weight houses less than store
    return store_diff + 0.1 * houses_diff

def sow_move(current_state, opponent_state, i):
    # Simulate sowing from house i in current_state
    current_state = current_state[:]  # Copy to avoid side effects
    opponent_state = opponent_state[:]
    seeds = current_state[i]
    if seeds == 0:
        return current_state, opponent_state, False  # Illegal move, but we assume valid
    current_state[i] = 0
    
    # Sowing sequence: current_state[0-6], opponent_state[0-5], repeat
    # Total pits: 13
    for k in range(seeds):
        pit_pos = (i + 1 + k) % 13
        if pit_pos <= 6:
            pit_idx = pit_pos
            is_house = pit_idx < 6
            was_empty = current_state[pit_idx] == 0 if is_house else False
            current_state[pit_idx] += 1
            if k == seeds - 1 and is_house and was_empty:
                opp_house_idx = 5 - pit_idx
                if opponent_state[opp_house_idx] > 0:
                    # Capture
                    current_state[6] += 1 + opponent_state[opp_house_idx]
                    current_state[pit_idx] = 0
                    opponent_state[opp_house_idx] = 0
        else:
            pit_idx = pit_pos - 7
            opponent_state[pit_idx] += 1
    
    # Check for extra turn
    extra_turn = False
    if seeds > 0:
        last_pit_pos = (i + 1 + seeds - 1) % 13
        if last_pit_pos == 6:  # Landed in store
            extra_turn = True
    
    return current_state, opponent_state, extra_turn

def minimax(my_state, opponent_state, depth, alpha, beta, is_my_turn):
    # Base case
    score = eval_state(my_state, opponent_state)
    if depth == 0 or abs(score) == 10000:
        return score
    
    if is_my_turn:
        best = -math.inf
        legal_moves = [i for i in range(6) if my_state[i] > 0]
        if not legal_moves:
            return score  # No moves, but game should be over already
        for i in legal_moves:
            new_my_state, new_opponent_state, extra_turn = sow_move(my_state, opponent_state, i)
            value = minimax(new_my_state, new_opponent_state, depth-1, alpha, beta, True if extra_turn else False)
            best = max(best, value)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        legal_moves = [i for i in range(6) if opponent_state[i] > 0]
        if not legal_moves:
            return score
        for i in legal_moves:
            # When opponent moves, we sow from opponent_state
            new_opponent_state, new_my_state, extra_turn = sow_move(opponent_state, my_state, i)
            # After sowing, the state is updated: current_state becomes new_opponent_state, opponent_state becomes new_my_state
            value = minimax(new_my_state, new_opponent_state, depth-1, alpha, beta, False if extra_turn else True)
            best = min(best, value)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(you, opponent):
    # Implement depth-limited minimax
    depth = 4
    alpha = -math.inf
    beta = math.inf
    best_move = None
    best_value = -math.inf
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    for i in legal_moves:
        new_you, new_opponent, extra_turn = sow_move(you, opponent, i)
        value = minimax(new_you, new_opponent, depth-1, alpha, beta, True if extra_turn else False)
        if value > best_value:
            best_value = value
            best_move = i
        alpha = max(alpha, best_value)
    
    return best_move
