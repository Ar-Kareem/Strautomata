
import time

def policy(you: list[int], opponent: list[int]) -> int:
    # Helper function to simulate a move
    def simulate_move(you_state, opp_state, house):
        """Return (new_you, new_opponent, extra_turn)"""
        you_copy = you_state[:]
        opp_copy = opp_state[:]
        seeds = you_copy[house]
        you_copy[house] = 0
        pos = house + 1
        player = 0  # 0: you, 1: opponent
        last_house = None
        last_player = None
        
        while seeds > 0:
            if player == 0:
                if pos <= 5:
                    you_copy[pos] += 1
                    last_house = pos
                    last_player = 0
                    seeds -= 1
                    pos += 1
                elif pos == 6:
                    you_copy[6] += 1
                    last_house = 6
                    last_player = 0
                    seeds -= 1
                    pos = 0
                    player = 1
                else:
                    pos = 0
                    player = 1
            else:  # player == 1 (opponent's side)
                if pos <= 5:
                    opp_copy[pos] += 1
                    last_house = pos
                    last_player = 1
                    seeds -= 1
                    pos += 1
                elif pos == 6:
                    # skip opponent's store
                    pos = 0
                    player = 0
                else:
                    pos = 0
                    player = 0
        
        extra_turn = (last_player == 0 and last_house == 6)
        
        # Capture rule
        if not extra_turn and last_player == 0 and 0 <= last_house <= 5:
            if you_copy[last_house] == 1:  # was empty before the drop
                opp_house = 5 - last_house
                if opp_copy[opp_house] > 0:
                    you_copy[6] += you_copy[last_house] + opp_copy[opp_house]
                    you_copy[last_house] = 0
                    opp_copy[opp_house] = 0
        
        return you_copy, opp_copy, extra_turn
    
    def evaluate(y_state, o_state):
        """Heuristic evaluation of the state"""
        store_diff = y_state[6] - o_state[6]
        house_diff = sum(y_state[0:6]) - sum(o_state[0:6])
        return store_diff + 0.1 * house_diff
    
    def is_terminal(y_state, o_state):
        return sum(y_state[0:6]) == 0 or sum(o_state[0:6]) == 0
    
    def terminal_score(y_state, o_state):
        """Score when game ends"""
        y_final = y_state[:]
        o_final = o_state[:]
        y_final[6] += sum(y_final[0:6])
        o_final[6] += sum(o_final[0:6])
        for i in range(6):
            y_final[i] = 0
            o_final[i] = 0
        return evaluate(y_final, o_final)
    
    # Minimax with alpha-beta pruning
    def minimax(y_state, o_state, depth, alpha, beta, maximizing):
        if is_terminal(y_state, o_state):
            return terminal_score(y_state, o_state)
        if depth == 0:
            return evaluate(y_state, o_state)
        
        if maximizing:
            legal = [i for i in range(6) if y_state[i] > 0]
            if not legal:
                return evaluate(y_state, o_state)
            # Sort moves by descending seeds (heuristic)
            legal.sort(key=lambda i: y_state[i], reverse=True)
            max_eval = -float('inf')
            for move in legal:
                new_y, new_o, extra = simulate_move(y_state, o_state, move)
                if extra:
                    eval = minimax(new_y, new_o, depth-1, alpha, beta, True)
                else:
                    eval = minimax(new_y, new_o, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Opponent's turn (minimizing player)
            legal = [i for i in range(6) if o_state[i] > 0]
            if not legal:
                return evaluate(y_state, o_state)
            legal.sort(key=lambda i: o_state[i], reverse=True)
            min_eval = float('inf')
            for move in legal:
                # Swap roles for simulation
                new_o, new_y, extra = simulate_move(o_state, y_state, move)
                if extra:
                    eval = minimax(new_y, new_o, depth-1, alpha, beta, False)
                else:
                    eval = minimax(new_y, new_o, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Main policy logic
    start = time.time()
    time_limit = 0.95  # seconds
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    depth = 1
    while time.time() - start < time_limit:
        best_score = -float('inf')
        current_best = best_move
        for move in legal_moves:
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            if extra:
                score = minimax(new_you, new_opp, depth-1, -float('inf'), float('inf'), True)
            else:
                score = minimax(new_you, new_opp, depth-1, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                current_best = move
        best_move = current_best
        depth += 1
        if depth > 20:
            break
    
    return best_move
