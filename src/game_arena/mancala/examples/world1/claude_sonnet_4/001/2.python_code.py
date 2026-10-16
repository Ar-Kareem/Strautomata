
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    
    start_time = time.time()
    
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return (new_you, new_opp, extra_turn, game_over)"""
        you_new = you_state[:]
        opp_new = opp_state[:]
        
        if you_new[move] == 0:
            return you_new, opp_new, False, False
        
        seeds = you_new[move]
        you_new[move] = 0
        pos = move
        
        # Distribute seeds
        for _ in range(seeds):
            pos += 1
            if pos <= 6:  # Still on our side
                you_new[pos] += 1
            elif pos <= 12:  # On opponent's side (but skip their store)
                if pos == 13:  # Would be opponent's store
                    pos = 0
                    you_new[pos] += 1
                else:
                    opp_new[pos - 7] += 1
            else:  # Wrap around
                pos = pos % 14
                if pos == 6:  # Our store
                    you_new[6] += 1
                elif pos < 6:  # Our houses
                    you_new[pos] += 1
                else:  # Opponent houses (pos 7-12 maps to 0-5)
                    opp_new[pos - 7] += 1
        
        # Check for extra turn (last seed in our store)
        extra_turn = (pos == 6)
        
        # Check for capture
        if not extra_turn and pos < 6 and you_new[pos] == 1 and opp_new[5 - pos] > 0:
            # Capture!
            captured = you_new[pos] + opp_new[5 - pos]
            you_new[6] += captured
            you_new[pos] = 0
            opp_new[5 - pos] = 0
        
        # Check game over
        game_over = (sum(you_new[:6]) == 0) or (sum(opp_new[:6]) == 0)
        
        return you_new, opp_new, extra_turn, game_over
    
    def evaluate_position(you_state, opp_state):
        """Evaluate position from our perspective"""
        # Check if game is over
        you_houses = sum(you_state[:6])
        opp_houses = sum(opp_state[:6])
        
        you_total = you_state[6]
        opp_total = opp_state[6]
        
        if you_houses == 0:
            opp_total += opp_houses
        elif opp_houses == 0:
            you_total += you_houses
        
        if you_houses == 0 or opp_houses == 0:
            # Game over
            if you_total > opp_total:
                return 1000
            elif opp_total > you_total:
                return -1000
            else:
                return 0
        
        # Heuristic evaluation
        score = 0
        
        # Store difference (most important)
        score += 4 * (you_state[6] - opp_state[6])
        
        # Seeds on our side vs their side
        score += (you_houses - opp_houses)
        
        # Bonus for potential extra moves
        for i in range(6):
            if you_state[i] > 0 and (i + you_state[i]) == 6:
                score += 3
        
        # Bonus for potential captures
        for i in range(6):
            if you_state[i] == 0 and opp_state[5-i] > 0:
                for j in range(6):
                    if you_state[j] > 0 and (j + you_state[j]) % 14 == i:
                        score += opp_state[5-i]
        
        return score
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing, is_extra_turn=False):
        """Minimax with alpha-beta pruning"""
        if time.time() - start_time > 0.9:  # Time cutoff
            return evaluate_position(you_state, opp_state)
        
        if depth == 0:
            return evaluate_position(you_state, opp_state)
        
        # Get legal moves
        if maximizing:
            legal_moves = [i for i in range(6) if you_state[i] > 0]
        else:
            legal_moves = [i for i in range(6) if opp_state[i] > 0]
        
        if not legal_moves:
            return evaluate_position(you_state, opp_state)
        
        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                new_you, new_opp, extra_turn, game_over = simulate_move(you_state, opp_state, move)
                
                if game_over:
                    eval_score = evaluate_position(new_you, new_opp)
                elif extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True, True)
                else:
                    eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, False, False)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_opp, new_you, extra_turn, game_over = simulate_move(opp_state, you_state, move)
                
                if game_over:
                    eval_score = evaluate_position(new_you, new_opp)
                elif extra_turn:
                    eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, False, True)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True, False)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Try different depths based on available time
    for depth in range(1, 10):
        if time.time() - start_time > 0.8:
            break
            
        current_best = legal_moves[0]
        current_best_score = float('-inf')
        
        for move in legal_moves:
            if time.time() - start_time > 0.8:
                break
                
            new_you, new_opp, extra_turn, game_over = simulate_move(you, opponent, move)
            
            if game_over:
                score = evaluate_position(new_you, new_opp)
            elif extra_turn:
                score = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), True, True)
            else:
                score = minimax(new_opp, new_you, depth, float('-inf'), float('inf'), False, False)
            
            if score > current_best_score:
                current_best_score = score
                current_best = move
        
        best_move = current_best
        best_score = current_best_score
    
    return best_move
