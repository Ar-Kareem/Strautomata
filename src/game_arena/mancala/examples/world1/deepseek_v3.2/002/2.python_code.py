
import copy
import math
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Choose the best move using minimax with alpha-beta pruning.
    """
    # Use iterative deepening with time limit
    start_time = time.time()
    time_limit = 0.95  # seconds, leave some margin
    max_depth = 1
    best_move = None
    
    # Order moves: try those that give extra moves or captures first
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0  # Should not happen as per problem statement
    
    # Heuristically order moves: extra moves first, then captures, then others
    def move_score(move):
        # Simulate quickly to see if it gives extra move or capture
        you_copy = you[:]
        opp_copy = opponent[:]
        extra, capture = simulate_quick(you_copy, opp_copy, move)
        score = 0
        if extra:
            score += 100
        if capture > 0:
            score += capture
        # Prefer moves that sow seeds into store
        # If the number of seeds in house equals distance to store, it lands in store
        dist_to_store = 6 - move
        if you[move] == dist_to_store:
            score += 50
        return score
    
    legal_moves.sort(key=move_score, reverse=True)
    
    # Initial best move is the first legal move (in case we run out of time)
    best_move = legal_moves[0]
    
    # Iterative deepening
    while time.time() - start_time < time_limit and max_depth <= 20:
        depth_best_move = None
        depth_best_score = -math.inf
        alpha = -math.inf
        beta = math.inf
        for move in legal_moves:
            new_you, new_opp, extra = make_move(you, opponent, move)
            if extra:
                # Extra move: same player moves again
                score = minimax(new_you, new_opp, max_depth-1, alpha, beta, True, start_time, time_limit)
            else:
                score = minimax(new_you, new_opp, max_depth-1, alpha, beta, False, start_time, time_limit)
            if score > depth_best_score:
                depth_best_score = score
                depth_best_move = move
            alpha = max(alpha, depth_best_score)
            if alpha >= beta:
                break
            # Check time
            if time.time() - start_time >= time_limit:
                break
        if time.time() - start_time >= time_limit:
            # Time's up, return best move found so far
            break
        best_move = depth_best_move
        max_depth += 1
    
    return best_move

def simulate_quick(you, opponent, move):
    """
    Quick simulation to check for extra move and capture without deep copying.
    Returns (extra, capture_seeds) where extra is True if extra move, capture_seeds is number of seeds captured.
    """
    seeds = you[move]
    you[move] = 0
    player = 0  # 0 for you, 1 for opponent
    pos = move + 1
    extra = False
    captured = 0
    last_house = None
    last_side = None
    
    while seeds > 0:
        if player == 0:
            if pos == 6:
                # Your store
                you[6] += 1
                seeds -= 1
                if seeds == 0:
                    # Last seed in store: extra move
                    extra = True
                    last_house = 6
                    last_side = 0
                pos = 0
                player = 1
            elif pos < 6:
                you[pos] += 1
                seeds -= 1
                if seeds == 0:
                    last_house = pos
                    last_side = 0
                pos += 1
        else:
            if pos == 6:
                # Opponent's store, skip
                pos = 0
                player = 0
            elif pos < 6:
                opponent[pos] += 1
                seeds -= 1
                if seeds == 0:
                    last_house = pos
                    last_side = 1
                pos += 1
    
    # Check for capture
    if last_side == 0 and last_house is not None and last_house < 6:
        if you[last_house] == 1:  # was empty before the drop? We added one, so now it's 1 if it was 0 before.
            # Actually we need to know if it was empty before. Since we added one, we can check if it became 1.
            # But we don't have the original state. We'll approximate: if after adding it's 1, then it was 0 before.
            opp_house = 5 - last_house
            if opponent[opp_house] > 0:
                captured = opponent[opp_house] + 1
                # Perform capture
                you[6] += captured
                you[last_house] = 0
                opponent[opp_house] = 0
    
    return extra, captured

def make_move(you, opponent, house):
    """
    Perform a move and return new state (you, opponent) and whether extra turn is granted.
    """
    you_copy = copy.deepcopy(you)
    opp_copy = copy.deepcopy(opponent)
    
    seeds = you_copy[house]
    you_copy[house] = 0
    player = 0  # 0 for you, 1 for opponent
    pos = house + 1
    extra = False
    
    while seeds > 0:
        if player == 0:
            if pos == 6:
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    extra = True
                pos = 0
                player = 1
            elif pos < 6:
                you_copy[pos] += 1
                seeds -= 1
                pos += 1
        else:
            if pos == 6:
                # Skip opponent's store
                pos = 0
                player = 0
            elif pos < 6:
                opp_copy[pos] += 1
                seeds -= 1
                pos += 1
    
    # Check for capture
    if not extra and pos > 0:
        # Determine where the last seed landed
        # We need to backtrack: we know seeds became 0 after adding one.
        # Actually we can compute by simulating again or keep track.
        # Let's compute by reversing the process: easier to track during the loop.
        # Instead, we'll recompute the last position.
        # But to avoid complexity, let's do a separate function for capture detection.
        pass
    
    # Now handle capture
    # We need to know the last house and side.
    # Let's do a separate simulation for capture detection.
    # Since we already have the board after sowing, we can determine by checking which house received the last seed.
    # But we don't have that information. So we'll do a second quick simulation or modify the above.
    # I'll modify the above loop to record last house and side.
    
    # Actually, let's redo with tracking.
    you_copy = copy.deepcopy(you)
    opp_copy = copy.deepcopy(opponent)
    
    seeds = you_copy[house]
    you_copy[house] = 0
    player = 0
    pos = house + 1
    extra = False
    last_house = None
    last_side = None
    
    while seeds > 0:
        if player == 0:
            if pos == 6:
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    extra = True
                    last_house = 6
                    last_side = 0
                pos = 0
                player = 1
            elif pos < 6:
                you_copy[pos] += 1
                seeds -= 1
                if seeds == 0:
                    last_house = pos
                    last_side = 0
                pos += 1
        else:
            if pos == 6:
                pos = 0
                player = 0
            elif pos < 6:
                opp_copy[pos] += 1
                seeds -= 1
                if seeds == 0:
                    last_house = pos
                    last_side = 1
                pos += 1
    
    # Capture
    if not extra and last_side == 0 and last_house < 6:
        if you_copy[last_house] == 1:  # it was empty before the drop
            opp_house = 5 - last_house
            if opp_copy[opp_house] > 0:
                # Capture
                you_copy[6] += you_copy[last_house] + opp_copy[opp_house]
                you_copy[last_house] = 0
                opp_copy[opp_house] = 0
    
    return you_copy, opp_copy, extra

def game_over(you, opponent):
    """Return True if the game is over."""
    return sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0

def evaluate(you, opponent):
    """
    Evaluate the board from the perspective of the player to move (maximizing player).
    """
    # If game is over, compute final score
    if sum(you[0:6]) == 0:
        # You have no seeds in houses, opponent moves remaining seeds to their store
        opp_remaining = sum(opponent[0:6])
        return you[6] - (opponent[6] + opp_remaining)
    if sum(opponent[0:6]) == 0:
        # Opponent has no seeds, you move remaining seeds to your store
        your_remaining = sum(you[0:6])
        return (you[6] + your_remaining) - opponent[6]
    
    # Heuristic: store difference plus 0.5 times the difference in seeds on sides
    store_diff = you[6] - opponent[6]
    side_diff = sum(you[0:6]) - sum(opponent[0:6])
    return store_diff + 0.5 * side_diff

def minimax(you, opponent, depth, alpha, beta, maximizing_player, start_time, time_limit):
    """
    Minimax with alpha-beta pruning.
    maximizing_player: True if it's the turn of the player we're optimizing for (the original player).
    """
    # Check time
    if time.time() - start_time >= time_limit:
        return evaluate(you, opponent)
    
    if depth == 0 or game_over(you, opponent):
        return evaluate(you, opponent)
    
    if maximizing_player:
        legal_moves = [i for i in range(6) if you[i] > 0]
        if not legal_moves:
            return evaluate(you, opponent)
        max_eval = -math.inf
        for move in legal_moves:
            new_you, new_opp, extra = make_move(you, opponent, move)
            if extra:
                eval = minimax(new_you, new_opp, depth-1, alpha, beta, True, start_time, time_limit)
            else:
                eval = minimax(new_you, new_opp, depth-1, alpha, beta, False, start_time, time_limit)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        # Minimizing player's turn (opponent)
        legal_moves = [i for i in range(6) if opponent[i] > 0]
        if not legal_moves:
            return evaluate(you, opponent)
        min_eval = math.inf
        for move in legal_moves:
            # Note: from opponent's perspective, their list is first.
            # So we swap the board for the move simulation.
            new_opp, new_you, extra = make_move(opponent, you, move)
            if extra:
                eval = minimax(new_you, new_opp, depth-1, alpha, beta, False, start_time, time_limit)
            else:
                eval = minimax(new_you, new_opp, depth-1, alpha, beta, True, start_time, time_limit)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

