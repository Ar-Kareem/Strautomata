
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        # Create copies to avoid modifying original states
        you_copy = you_state[:]
        opp_copy = opp_state[:]
        
        # Pick up seeds from chosen house
        seeds = you_copy[move]
        you_copy[move] = 0
        
        # Track position for seed placement
        pos = move + 1
        extra_turn = False
        
        # Distribute seeds
        while seeds > 0:
            if pos < 6:  # Your houses 1-5
                you_copy[pos] += 1
                last_pos = ('you', pos)
            elif pos == 6:  # Your store
                you_copy[6] += 1
                last_pos = ('you', 6)
                if seeds == 1:  # Last seed in store = extra turn
                    extra_turn = True
            elif pos < 12:  # Opponent houses 0-5
                opp_idx = pos - 7
                opp_copy[opp_idx] += 1
                last_pos = ('opp', opp_idx)
            else:  # Opponent house 5, wrap around
                pos = 0
                you_copy[0] += 1
                last_pos = ('you', 0)
            
            seeds -= 1
            pos += 1
            if pos == 13:  # Skip opponent store and wrap
                pos = 0
        
        # Check for capture
        if (last_pos[0] == 'you' and last_pos[1] < 6 and 
            you_copy[last_pos[1]] == 1 and opp_copy[5 - last_pos[1]] > 0):
            # Capture
            captured = opp_copy[5 - last_pos[1]]
            you_copy[6] += captured + 1  # Captured seeds + the seed that landed
            you_copy[last_pos[1]] = 0
            opp_copy[5 - last_pos[1]] = 0
        
        return you_copy, opp_copy, extra_turn
    
    def evaluate_position(you_state, opp_state):
        # Simple evaluation: store difference + mobility
        store_diff = you_state[6] - opp_state[6]
        
        # Count available moves (mobility)
        your_moves = sum(1 for i in range(6) if you_state[i] > 0)
        opp_moves = sum(1 for i in range(6) if opp_state[i] > 0)
        mobility = your_moves - opp_moves
        
        # Bonus for seeds closer to store
        position_bonus = sum(you_state[i] * (6-i) for i in range(6)) / 10
        
        return store_diff + mobility * 2 + position_bonus
    
    def minimax(you_state, opp_state, depth, alpha, beta, is_maximizing, your_turn):
        # Check if game is over
        you_empty = all(you_state[i] == 0 for i in range(6))
        opp_empty = all(opp_state[i] == 0 for i in range(6))
        
        if you_empty or opp_empty or depth == 0:
            final_you = you_state[:]
            final_opp = opp_state[:]
            
            if you_empty:
                final_opp[6] += sum(opp_state[:6])
            elif opp_empty:
                final_you[6] += sum(you_state[:6])
            
            return final_you[6] - final_opp[6]
        
        if is_maximizing:
            max_eval = float('-inf')
            moves = [i for i in range(6) if you_state[i] > 0]
            
            for move in moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True, True)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, False, False)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval
        else:
            min_eval = float('inf')
            moves = [i for i in range(6) if opp_state[i] > 0]
            
            for move in moves:
                new_opp, new_you, extra_turn = simulate_move(opp_state, you_state, move)
                
                if extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, False, False)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval
    
    # Find all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Try each legal move
    for move in legal_moves:
        new_you, new_opp, extra_turn = simulate_move(you, opponent, move)
        
        # Use minimax with alpha-beta pruning
        if extra_turn:
            score = minimax(new_you, new_opp, 6, float('-inf'), float('inf'), True, True)
        else:
            score = minimax(new_you, new_opp, 6, float('-inf'), float('inf'), False, False)
        
        # Bonus for moves that give extra turns or captures
        if extra_turn:
            score += 5
        
        # Check for immediate capture
        if move < 6 and you[move] > 0:
            final_pos = (move + you[move]) % 13
            if final_pos < 6 and you[final_pos] == 0 and opponent[5 - final_pos] > 0:
                score += opponent[5 - final_pos] + 2
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
