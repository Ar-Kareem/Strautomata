
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return new state and whether we get extra turn."""
        you = you_state[:]
        opp = opp_state[:]
        
        seeds = you[move]
        you[move] = 0
        
        # Track position in circular board
        pos = move
        player_side = 'you'
        
        while seeds > 0:
            pos += 1
            
            if player_side == 'you':
                if pos <= 5:
                    # Your houses
                    you[pos] += 1
                    seeds -= 1
                    last_side, last_pos = 'you', pos
                elif pos == 6:
                    # Your store
                    you[6] += 1
                    seeds -= 1
                    last_side, last_pos = 'you', 6
                else:
                    # Switch to opponent side
                    player_side = 'opp'
                    pos = -1
            else:  # player_side == 'opp'
                if pos <= 5:
                    # Opponent houses
                    opp[pos] += 1
                    seeds -= 1
                    last_side, last_pos = 'opp', pos
                else:
                    # Skip opponent store, switch back to your side
                    player_side = 'you'
                    pos = -1
        
        # Check for extra turn
        extra_turn = (last_side == 'you' and last_pos == 6)
        
        # Check for capture
        if last_side == 'you' and 0 <= last_pos <= 5:
            if you[last_pos] == 1:  # Was empty before the last seed
                opposite = 5 - last_pos
                if opp[opposite] > 0:
                    # Capture
                    you[6] += you[last_pos] + opp[opposite]
                    you[last_pos] = 0
                    opp[opposite] = 0
        
        return you, opp, extra_turn
    
    def is_terminal(you_state, opp_state):
        return sum(you_state[:6]) == 0 or sum(opp_state[:6]) == 0
    
    def evaluate(you_state, opp_state):
        """Evaluate position from current player's perspective."""
        you_score = you_state[6]
        opp_score = opp_state[6]
        
        # If terminal, add remaining seeds
        if sum(you_state[:6]) == 0:
            opp_score += sum(opp_state[:6])
        elif sum(opp_state[:6]) == 0:
            you_score += sum(you_state[:6])
        
        return you_score - opp_score
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0 or is_terminal(you_state, opp_state):
            return evaluate(you_state, opp_state), None
        
        legal_moves = [i for i in range(6) if you_state[i] > 0]
        
        if not legal_moves:
            return evaluate(you_state, opp_state), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = legal_moves[0]
            
            # Prioritize moves that give extra turns
            def move_priority(m):
                # Moves that land in store come first
                if you_state[m] == 6 - m:
                    return 0
                return 1
            
            legal_moves.sort(key=move_priority)
            
            for move in legal_moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    # We move again
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
                    # Opponent moves
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
            
            for move in legal_moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, None
    
    # Try increasing depths
    best_move = None
    for depth in range(1, 12):
        _, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    # Safety fallback
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
    
    return best_move
