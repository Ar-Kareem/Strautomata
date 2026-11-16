
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return (new_you, new_opp, extra_turn)"""
        you = you_state[:]
        opp = opp_state[:]
        
        if you[move] == 0:
            return you, opp, False
            
        seeds = you[move]
        you[move] = 0
        
        pos = move
        extra_turn = False
        
        # Distribute seeds
        for _ in range(seeds):
            pos += 1
            if pos <= 5:  # My houses
                you[pos] += 1
            elif pos == 6:  # My store
                you[pos] += 1
            elif pos <= 12:  # Opponent houses (7-12 -> 0-5)
                opp[pos - 7] += 1
            else:  # Wrap around to my houses
                pos = pos % 13
                you[pos] += 1
        
        # Check for extra turn
        if pos == 6:
            extra_turn = True
        
        # Check for capture
        elif 0 <= pos <= 5 and you[pos] == 1 and opp[5 - pos] > 0:
            # Capture
            captured = opp[5 - pos]
            opp[5 - pos] = 0
            you[6] += captured + 1
            you[pos] = 0
        
        return you, opp, extra_turn
    
    def is_game_over(you_state, opp_state):
        """Check if game is over"""
        you_empty = sum(you_state[:6]) == 0
        opp_empty = sum(opp_state[:6]) == 0
        return you_empty or opp_empty
    
    def final_score(you_state, opp_state):
        """Calculate final scores when game ends"""
        you_final = you_state[:]
        opp_final = opp_state[:]
        
        # Move remaining seeds to stores
        you_final[6] += sum(you_final[:6])
        opp_final[6] += sum(opp_final[:6])
        
        return you_final[6] - opp_final[6]
    
    def evaluate(you_state, opp_state, depth):
        """Evaluate position from my perspective"""
        if is_game_over(you_state, opp_state):
            return final_score(you_state, opp_state) * 1000
        
        # Store advantage (most important)
        store_diff = you_state[6] - opp_state[6]
        
        # Material advantage
        my_seeds = sum(you_state[:6])
        opp_seeds = sum(opp_state[:6])
        material_diff = my_seeds - opp_seeds
        
        # Potential captures
        capture_value = 0
        for i in range(6):
            if you_state[i] == 0 and opp_state[5-i] > 0:
                capture_value += opp_state[5-i] * 0.1
        
        # Potential extra moves
        extra_move_value = 0
        for i in range(6):
            if you_state[i] > 0:
                final_pos = (i + you_state[i]) % 13
                if final_pos == 6:
                    extra_move_value += 0.5
        
        return store_diff * 10 + material_diff * 0.1 + capture_value + extra_move_value
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing, my_turn):
        """Minimax with alpha-beta pruning"""
        if depth == 0 or is_game_over(you_state, opp_state):
            return evaluate(you_state, opp_state, depth)
        
        if maximizing:
            max_eval = float('-inf')
            # Try all possible moves for current player
            current_state = you_state if my_turn else opp_state
            for move in range(6):
                if current_state[move] > 0:
                    if my_turn:
                        new_you, new_opp, extra = simulate_move(you_state, opp_state, move)
                        if extra:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, True, True)
                        else:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, False, False)
                    else:
                        new_opp, new_you, extra = simulate_move(opp_state, you_state, move)
                        if extra:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, True, False)
                        else:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, False, True)
                    
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            current_state = you_state if my_turn else opp_state
            for move in range(6):
                if current_state[move] > 0:
                    if my_turn:
                        new_you, new_opp, extra = simulate_move(you_state, opp_state, move)
                        if extra:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, False, True)
                        else:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, True, False)
                    else:
                        new_opp, new_you, extra = simulate_move(opp_state, you_state, move)
                        if extra:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, False, False)
                        else:
                            eval_score = minimax(new_you, new_opp, depth-1, alpha, beta, True, True)
                    
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval
    
    # Find best move using minimax
    best_move = 0
    best_score = float('-inf')
    
    # Try different depths based on game complexity
    total_seeds = sum(you) + sum(opponent)
    if total_seeds < 20:
        depth = 10
    elif total_seeds < 30:
        depth = 8
    else:
        depth = 6
    
    for move in range(6):
        if you[move] > 0:
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            if extra:
                score = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), True, True)
            else:
                score = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), False, False)
            
            if score > best_score:
                best_score = score
                best_move = move
    
    return best_move
