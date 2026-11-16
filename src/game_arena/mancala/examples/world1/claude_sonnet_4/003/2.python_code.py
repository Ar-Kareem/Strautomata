
def policy(you: list[int], opponent: list[int]) -> int:
    import copy
    
    def get_legal_moves(player_houses):
        return [i for i in range(6) if player_houses[i] > 0]
    
    def simulate_move(you_state, opp_state, move):
        # Create copies to avoid modifying original state
        you = you_state[:]
        opponent = opp_state[:]
        
        # Pick up seeds from chosen house
        seeds = you[move]
        you[move] = 0
        
        # Distribute seeds
        pos = move
        player_side = True  # True for you, False for opponent
        
        for _ in range(seeds):
            pos += 1
            
            if player_side:
                if pos <= 5:
                    # Still in your houses
                    you[pos] += 1
                elif pos == 6:
                    # Your store
                    you[pos] += 1
                else:
                    # Switch to opponent side
                    player_side = False
                    pos = 0
                    opponent[pos] += 1
            else:
                if pos <= 5:
                    # Opponent's houses
                    opponent[pos] += 1
                else:
                    # Switch back to your side (skip opponent's store)
                    player_side = True
                    pos = 0
                    you[pos] += 1
        
        # Check for extra turn (last seed in your store)
        extra_turn = player_side and pos == 6
        
        # Check for capture
        captured = False
        if player_side and 0 <= pos <= 5 and you[pos] == 1 and opponent[5 - pos] > 0:
            # Capture
            captured_seeds = you[pos] + opponent[5 - pos]
            you[6] += captured_seeds
            you[pos] = 0
            opponent[5 - pos] = 0
            captured = True
        
        return you, opponent, extra_turn, captured
    
    def evaluate_position(you_state, opp_state):
        # Simple evaluation: score difference plus positional factors
        score_diff = you_state[6] - opp_state[6]
        
        # Bonus for seeds closer to store (they're easier to score)
        positional_bonus = sum(you_state[i] * (6 - i) for i in range(6)) * 0.1
        positional_penalty = sum(opp_state[i] * (6 - i) for i in range(6)) * 0.1
        
        # Penalty for giving opponent many seeds in houses close to their store
        opp_threat = sum(opp_state[i] * (i + 1) for i in range(6)) * 0.05
        
        return score_diff + positional_bonus - positional_penalty - opp_threat
    
    def minimax(you_state, opp_state, depth, maximizing_player, alpha=float('-inf'), beta=float('inf')):
        # Check if game is over
        you_empty = all(you_state[i] == 0 for i in range(6))
        opp_empty = all(opp_state[i] == 0 for i in range(6))
        
        if depth == 0 or you_empty or opp_empty:
            # End game scoring if houses are empty
            if you_empty or opp_empty:
                final_you = you_state[:]
                final_opp = opp_state[:]
                final_you[6] += sum(you_state[i] for i in range(6))
                final_opp[6] += sum(opp_state[i] for i in range(6))
                return final_you[6] - final_opp[6], None
            else:
                return evaluate_position(you_state, opp_state), None
        
        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            legal_moves = get_legal_moves(you_state)
            
            for move in legal_moves:
                new_you, new_opp, extra_turn, captured = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    # Same player moves again
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
                else:
                    # Opponent's turn
                    eval_score, _ = minimax(new_opp, new_you, depth - 1, False, alpha, beta)
                
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
            legal_moves = get_legal_moves(opp_state)
            
            for move in legal_moves:
                new_opp, new_you, extra_turn, captured = simulate_move(opp_state, you_state, move)
                
                if extra_turn:
                    # Same player (opponent) moves again
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
                else:
                    # Your turn
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Get legal moves
    legal_moves = get_legal_moves(you)
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Try minimax with limited depth
    try:
        _, best_move = minimax(you, opponent, 4, True)
        if best_move is not None:
            return best_move
    except:
        pass
    
    # Fallback: evaluate each move directly
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra_turn, captured = simulate_move(you, opponent, move)
        
        # Score this move
        score = evaluate_position(new_you, new_opp)
        
        # Bonus for extra turns and captures
        if extra_turn:
            score += 5
        if captured:
            score += 3
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
