
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Select the best move for Kalah using minimax with alpha-beta pruning.
    """
    
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return the new state and whether we get another turn."""
        you = you_state[:]
        opp = opp_state[:]
        
        seeds = you[move]
        you[move] = 0
        pos = move
        
        # Distribute seeds
        while seeds > 0:
            pos += 1
            
            # In your houses
            if pos <= 5:
                you[pos] += 1
                seeds -= 1
            # In your store
            elif pos == 6:
                you[6] += 1
                seeds -= 1
            # In opponent's houses
            elif pos <= 12:
                opp[pos - 7] += 1
                seeds -= 1
            # Wrap around to your houses
            else:
                pos = -1
                continue
        
        # Check for extra turn (last seed in store)
        extra_turn = (pos == 6)
        
        # Check for capture
        if not extra_turn and 0 <= pos <= 5 and you[pos] == 1 and opp[5 - pos] > 0:
            you[6] += you[pos] + opp[5 - pos]
            you[pos] = 0
            opp[5 - pos] = 0
        
        return you, opp, extra_turn
    
    def is_terminal(you_state, opp_state):
        """Check if the game is over."""
        return sum(you_state[:6]) == 0 or sum(opp_state[:6]) == 0
    
    def get_final_score(you_state, opp_state):
        """Get final score difference."""
        you_final = you_state[:]
        opp_final = opp_state[:]
        
        you_final[6] += sum(you_final[:6])
        opp_final[6] += sum(opp_final[:6])
        
        return you_final[6] - opp_final[6]
    
    def evaluate(you_state, opp_state):
        """Evaluate the board state."""
        if is_terminal(you_state, opp_state):
            return get_final_score(you_state, opp_state)
        
        # Score difference plus positional bonuses
        score_diff = you_state[6] - opp_state[6]
        
        # Bonus for seeds closer to store (more likely to score)
        positional = sum((6 - i) * you_state[i] for i in range(6))
        positional -= sum((6 - i) * opp_state[i] for i in range(6))
        
        return score_diff + 0.1 * positional
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0 or is_terminal(you_state, opp_state):
            return evaluate(you_state, opp_state), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = None
            
            for move in range(6):
                if you_state[move] > 0:
                    new_you, new_opp, extra = simulate_move(you_state, opp_state, move)
                    
                    if extra:
                        # We get another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                    else:
                        # Opponent's turn
                        eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                        eval_score = -eval_score
                    
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
                    new_you, new_opp, extra = simulate_move(you_state, opp_state, move)
                    
                    if extra:
                        # Current player gets another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                    else:
                        # Switch back to maximizing player
                        eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, True)
                        eval_score = -eval_score
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            
            return min_eval, best_move
    
    # Use depth 8 for good balance of strength and speed
    _, best_move = minimax(you, opponent, 8, float('-inf'), float('inf'), True)
    
    # Fallback to first legal move if minimax fails
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
    
    return best_move
