
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        """
        Simulate a move and return new state, extra_move flag, and if game ended
        Returns: (new_you, new_opp, got_extra_move, game_over)
        """
        you = you_state[:]
        opp = opp_state[:]
        
        seeds = you[move]
        you[move] = 0
        
        pos = move
        side = 'you'
        
        while seeds > 0:
            pos += 1
            
            if side == 'you':
                if pos <= 5:
                    you[pos] += 1
                    seeds -= 1
                elif pos == 6:
                    you[6] += 1
                    seeds -= 1
                else:
                    side = 'opp'
                    pos = -1
            else:  # side == 'opp'
                if pos <= 5:
                    opp[pos] += 1
                    seeds -= 1
                else:
                    side = 'you'
                    pos = -1
        
        # Check for extra move
        extra_move = (side == 'you' and pos == 6)
        
        # Check for capture
        if not extra_move and side == 'you' and 0 <= pos <= 5:
            if you[pos] == 1 and opp[5 - pos] > 0:  # Was empty before drop
                you[6] += you[pos] + opp[5 - pos]
                you[pos] = 0
                opp[5 - pos] = 0
        
        # Check if game over
        you_empty = all(you[i] == 0 for i in range(6))
        opp_empty = all(opp[i] == 0 for i in range(6))
        
        game_over = you_empty or opp_empty
        
        if game_over:
            # Move remaining seeds to stores
            for i in range(6):
                you[6] += you[i]
                you[i] = 0
                opp[6] += opp[i]
                opp[i] = 0
        
        return you, opp, extra_move, game_over
    
    def evaluate(you_state, opp_state):
        """Evaluate the board state from original 'you' perspective"""
        return you_state[6] - opp_state[6]
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing):
        """
        Minimax with alpha-beta pruning
        maximizing=True means it's current 'you_state' player's turn
        Always evaluate from original caller's perspective
        """
        # Check if game is over
        you_empty = all(you_state[i] == 0 for i in range(6))
        opp_empty = all(opp_state[i] == 0 for i in range(6))
        
        if depth == 0 or you_empty or opp_empty:
            return evaluate(you_state, opp_state), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = None
            
            for move in range(6):
                if you_state[move] > 0:
                    new_you, new_opp, extra_move, game_over = simulate_move(you_state, opp_state, move)
                    
                    if extra_move and not game_over:
                        # Same player gets another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                    else:
                        # Switch to opponent's turn
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
            best_move = None
            
            for move in range(6):
                if you_state[move] > 0:
                    new_you, new_opp, extra_move, game_over = simulate_move(you_state, opp_state, move)
                    
                    if extra_move and not game_over:
                        # Same player (opponent) gets another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                    else:
                        # Switch back to maximizing player's turn
                        eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, True)
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            
            return min_eval, best_move
    
    # Try to find best move with minimax
    _, best_move = minimax(you, opponent, depth=10, alpha=float('-inf'), beta=float('inf'), maximizing=True)
    
    # Fallback to first legal move if something went wrong
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
    
    return best_move
