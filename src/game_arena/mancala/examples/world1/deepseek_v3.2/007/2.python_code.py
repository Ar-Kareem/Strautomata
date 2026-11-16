
import time
import math

def simulate_move(you, opponent, move):
    """
    Simulate a move from house 'move' (0-5) for the player with 'you' state.
    Returns (new_you, new_opponent, extra_move).
    """
    you_copy = you.copy()
    opponent_copy = opponent.copy()
    
    seeds = you_copy[move]
    you_copy[move] = 0
    
    # Start sowing from the next house
    index = move + 1
    is_my_side = True
    
    last_house_index = None
    last_was_my_side = None
    last_was_store = False
    
    while seeds > 0:
        if is_my_side:
            if index == 6:  # my store
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    last_was_store = True
                    last_was_my_side = True
                    last_house_index = 6
                index = 0
                is_my_side = False  # after store, go to opponent side
            else:  # my house 0-5
                you_copy[index] += 1
                seeds -= 1
                if seeds == 0:
                    last_was_store = False
                    last_was_my_side = True
                    last_house_index = index
                index += 1
                if index == 7:  # wrap to opponent after house 5
                    index = 0
                    is_my_side = False
        else:  # opponent side
            if index == 6:  # opponent store, skip
                index = 0
                is_my_side = True
                continue
            else:  # opponent house 0-5
                opponent_copy[index] += 1
                seeds -= 1
                if seeds == 0:
                    last_was_store = False
                    last_was_my_side = False
                    last_house_index = index
                index += 1
                if index == 7:  # wrap to my side after house 5
                    index = 0
                    is_my_side = True
    
    # Check for capture
    if last_was_my_side and not last_was_store and last_house_index < 6:
        if you_copy[last_house_index] == 1:  # was empty before the drop
            opposite = 5 - last_house_index
            if opponent_copy[opposite] > 0:
                # Capture both the last seed and the opposite seeds
                you_copy[6] += you_copy[last_house_index] + opponent_copy[opposite]
                you_copy[last_house_index] = 0
                opponent_copy[opposite] = 0
    
    extra_move = last_was_store
    return you_copy, opponent_copy, extra_move

def evaluate(you, opponent):
    """
    Evaluate the state from the perspective of the player whose turn it is.
    Positive values are good for the current player.
    """
    # Store difference is most important
    store_diff = you[6] - opponent[6]
    
    # Seeds in houses: mine are potential future stores, opponent's are potential captures
    my_houses = sum(you[0:6])
    opp_houses = sum(opponent[0:6])
    
    # Heuristic: having more seeds in houses is good, but opponent's seeds are a threat
    house_value = my_houses - opp_houses * 0.7
    
    # Bonus for having potential extra moves (houses with enough seeds to reach store)
    extra_move_potential = 0
    for i in range(6):
        if you[i] > 0 and (you[i] == 6 - i or you[i] % 13 == (6 - i) % 13):
            extra_move_potential += 0.5
    
    # Bonus for capture opportunities
    capture_potential = 0
    for i in range(6):
        if you[i] == 0 and opponent[5 - i] > 0:
            # This house is empty, opponent has seeds opposite
            # Check if any of my houses can land here
            for j in range(6):
                if you[j] > 0:
                    distance = (j - i) % 12  # simplified
                    if you[j] == distance or (you[j] > distance and (you[j] - distance) % 12 == 0):
                        capture_potential += 0.3 * opponent[5 - i]
                        break
    
    return store_diff + house_value * 0.1 + extra_move_potential + capture_potential

def game_over(you, opponent):
    """Check if the game has ended."""
    return sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0

def finalize_game(you, opponent):
    """Move all remaining seeds to stores and return final state."""
    you_final = you.copy()
    opponent_final = opponent.copy()
    you_final[6] += sum(you_final[0:6])
    opponent_final[6] += sum(opponent_final[0:6])
    for i in range(6):
        you_final[i] = 0
        opponent_final[i] = 0
    return you_final, opponent_final

def minimax(you, opponent, depth, alpha, beta, maximizing_player, max_depth, start_time, time_limit):
    """
    Minimax with alpha-beta pruning.
    Returns (value, best_move) for the current player.
    """
    # Time check
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    
    # Check if game ended
    if game_over(you, opponent):
        you_final, opponent_final = finalize_game(you, opponent)
        return evaluate(you_final, opponent_final), None
    
    if depth >= max_depth:
        return evaluate(you, opponent), None
    
    if maximizing_player:
        best_value = -math.inf
        best_move = None
        
        # Get legal moves
        legal_moves = [i for i in range(6) if you[i] > 0]
        
        # Move ordering: try extra moves first, then captures
        def move_score(move):
            you_test, opp_test, extra = simulate_move(you, opponent, move)
            score = 0
            if extra:
                score += 100
            # Check if capture happens
            if extra:
                # Already accounted
                pass
            else:
                # Simple capture check (not perfect but fast)
                last_pos = (move + you[move]) % 12
                if last_pos < 6 and you_test[last_pos] == 1 and opp_test[5 - last_pos] > 0:
                    score += 50
            return score
        
        legal_moves.sort(key=move_score, reverse=True)
        
        for move in legal_moves:
            new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
            
            if extra_move:
                # Still my turn
                value, _ = minimax(new_you, new_opponent, depth, alpha, beta, True, max_depth, start_time, time_limit)
            else:
                # Opponent's turn
                value, _ = minimax(new_you, new_opponent, depth + 1, alpha, beta, False, max_depth, start_time, time_limit)
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        
        return best_value, best_move
    else:
        # Minimizing player (opponent)
        best_value = math.inf
        best_move = None
        
        # Get opponent's legal moves
        legal_moves = [i for i in range(6) if opponent[i] > 0]
        
        # Move ordering for opponent (we want to explore bad moves for us first)
        def move_score_opp(move):
            opp_test, you_test, extra = simulate_move(opponent, you, move)
            score = 0
            if extra:
                score -= 100  # opponent extra move is bad for us
            return score
        
        legal_moves.sort(key=move_score_opp)
        
        for move in legal_moves:
            # Simulate opponent's move (swap perspective)
            new_opponent, new_you, extra_move = simulate_move(opponent, you, move)
            
            if extra_move:
                # Opponent gets another move
                value, _ = minimax(new_you, new_opponent, depth + 1, alpha, beta, False, max_depth, start_time, time_limit)
            else:
                # My turn
                value, _ = minimax(new_you, new_opponent, depth + 1, alpha, beta, True, max_depth, start_time, time_limit)
            
            if value < best_value:
                best_value = value
                best_move = move
            
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        
        return best_value, best_move

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Policy function that returns a move (0-5) for the current player.
    Uses iterative deepening minimax with alpha-beta pruning.
    """
    start_time = time.time()
    time_limit = 0.95  # seconds, leave some margin
    
    best_move = None
    max_depth = 1
    
    # Iterative deepening
    while True:
        try:
            value, move = minimax(you, opponent, 0, -math.inf, math.inf, True, max_depth, start_time, time_limit)
            if move is not None:
                best_move = move
        except TimeoutError:
            break
        
        max_depth += 1
        if time.time() - start_time > time_limit:
            break
    
    # Fallback: choose first legal move if something went wrong
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                best_move = i
                break
    
    return best_move
