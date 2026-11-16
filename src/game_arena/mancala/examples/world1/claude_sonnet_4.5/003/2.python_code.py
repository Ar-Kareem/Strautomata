
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    TIME_LIMIT = 0.95  # Leave some margin
    
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return new state, whether we get extra turn"""
        you = you_state[:]
        opp = opp_state[:]
        
        seeds = you[move]
        you[move] = 0
        
        # Distribute seeds
        current_pos = move
        on_your_side = True
        
        while seeds > 0:
            current_pos += 1
            
            if on_your_side:
                if current_pos <= 6:
                    you[current_pos] += 1
                    last_pos = current_pos
                    last_side = True
                    seeds -= 1
                else:
                    on_your_side = False
                    current_pos = -1
            else:
                if current_pos <= 5:
                    opp[current_pos] += 1
                    last_pos = current_pos
                    last_side = False
                    seeds -= 1
                else:
                    on_your_side = True
                    current_pos = -1
        
        # Check for extra move (last seed in your store)
        extra_move = (last_side and last_pos == 6)
        
        # Check for capture (last seed in empty house on your side)
        if last_side and 0 <= last_pos <= 5 and you[last_pos] == 1:
            opposite_pos = 5 - last_pos
            if opp[opposite_pos] > 0:
                you[6] += you[last_pos] + opp[opposite_pos]
                you[last_pos] = 0
                opp[opposite_pos] = 0
        
        return you, opp, extra_move
    
    def is_terminal(you_state, opp_state):
        return sum(you_state[:6]) == 0 or sum(opp_state[:6]) == 0
    
    def final_score(you_state, opp_state):
        """Calculate final score difference"""
        you_total = you_state[6]
        opp_total = opp_state[6]
        
        if sum(you_state[:6]) == 0:
            opp_total += sum(opp_state[:6])
        else:
            you_total += sum(you_state[:6])
        
        return you_total - opp_total
    
    def evaluate(you_state, opp_state):
        """Evaluate position from your perspective"""
        if is_terminal(you_state, opp_state):
            return final_score(you_state, opp_state) * 1000
        
        # Main component: store difference
        score = (you_state[6] - opp_state[6]) * 10
        
        # Secondary: seeds on board
        score += sum(you_state[:6]) - sum(opp_state[:6])
        
        return score
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        if time.time() - start_time > TIME_LIMIT:
            return evaluate(you_state, opp_state), None
        
        if depth == 0 or is_terminal(you_state, opp_state):
            return evaluate(you_state, opp_state), None
        
        legal_moves = [i for i in range(6) if you_state[i] > 0] if maximizing else [i for i in range(6) if opp_state[i] > 0]
        
        if not legal_moves:
            return evaluate(you_state, opp_state), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = legal_moves[0]
            
            for move in legal_moves:
                new_you, new_opp, extra = simulate_move(you_state, opp_state, move)
                
                if extra and not is_terminal(new_you, new_opp):
                    # Extra turn for us
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
                    # Opponent's turn
                    eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = legal_moves[0]
            
            for move in legal_moves:
                new_opp, new_you, extra = simulate_move(opp_state, you_state, move)
                
                if extra and not is_terminal(new_opp, new_you):
                    # Extra turn for opponent
                    eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                else:
                    # Our turn
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Iterative deepening
    best_move = None
    for depth in range(1, 20):
        if time.time() - start_time > TIME_LIMIT:
            break
        _, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    # Fallback to first legal move
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                best_move = i
                break
    
    return best_move
