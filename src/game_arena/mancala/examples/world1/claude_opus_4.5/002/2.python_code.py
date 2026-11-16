
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    
    def simulate_move(you, opponent, move):
        """Simulate a move and return (new_you, new_opponent, extra_turn)"""
        you = list(you)
        opponent = list(opponent)
        
        seeds = you[move]
        you[move] = 0
        
        pos = move
        
        while seeds > 0:
            pos = (pos + 1) % 13
            
            if pos <= 5:
                you[pos] += 1
            elif pos == 6:
                you[6] += 1
            else:  # 7-12
                opponent[pos - 7] += 1
            
            seeds -= 1
        
        # Check where last seed landed
        extra_turn = (pos == 6)
        
        if 0 <= pos <= 5 and you[pos] == 1:
            opposite = 5 - pos
            if opponent[opposite] > 0:
                you[6] += you[pos] + opponent[opposite]
                you[pos] = 0
                opponent[opposite] = 0
        
        return you, opponent, extra_turn
    
    def game_over(you, opponent):
        return sum(you[:6]) == 0 or sum(opponent[:6]) == 0
    
    def final_score(you, opponent):
        return (you[6] + sum(you[:6])) - (opponent[6] + sum(opponent[:6]))
    
    def evaluate(you, opponent):
        """Heuristic evaluation"""
        score = you[6] - opponent[6]
        # Add small bonus for seeds on our side vs their side
        score += 0.1 * (sum(you[:6]) - sum(opponent[:6]))
        return score
    
    def minimax(you, opponent, depth, alpha, beta, is_our_turn):
        if game_over(you, opponent):
            return final_score(you, opponent)
        
        if depth == 0:
            return evaluate(you, opponent)
        
        if is_our_turn:
            max_eval = float('-inf')
            for move in range(6):
                if you[move] > 0:
                    new_you, new_opp, extra = simulate_move(you, opponent, move)
                    if extra:
                        ev = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                    else:
                        ev = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, ev)
                    alpha = max(alpha, ev)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for move in range(6):
                if opponent[move] > 0:
                    new_opp, new_you, extra = simulate_move(opponent, you, move)
                    if extra:
                        ev = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                    else:
                        ev = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, ev)
                    beta = min(beta, ev)
                    if beta <= alpha:
                        break
            return min_eval
    
    def get_legal_moves(you):
        return [i for i in range(6) if you[i] > 0]
    
    legal_moves = get_legal_moves(you)
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Iterative deepening
    best_move = legal_moves[0]
    start_time = time.time()
    time_limit = 0.9  # Leave some margin
    
    for depth in range(1, 20):
        if time.time() - start_time > time_limit:
            break
        
        current_best_move = legal_moves[0]
        current_best_eval = float('-inf')
        
        for move in legal_moves:
            if time.time() - start_time > time_limit:
                break
                
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            
            if extra:
                ev = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), True)
            else:
                ev = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), False)
            
            if ev > current_best_eval:
                current_best_eval = ev
                current_best_move = move
        
        best_move = current_best_move
    
    return best_move
