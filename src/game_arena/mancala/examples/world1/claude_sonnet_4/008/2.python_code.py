
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return the resulting state and whether we get extra turn"""
        you = you_state.copy()
        opponent = opp_state.copy()
        
        seeds = you[move]
        you[move] = 0
        
        pos = move + 1
        player = 0  # 0 = you, 1 = opponent
        
        extra_turn = False
        
        for _ in range(seeds):
            if player == 0:  # placing in your side
                if pos <= 5:  # in houses
                    you[pos] += 1
                    last_pos = pos
                    last_player = 0
                elif pos == 6:  # in your store
                    you[6] += 1
                    last_pos = 6
                    last_player = 0
                else:  # switch to opponent side
                    player = 1
                    pos = 0
                    opponent[pos] += 1
                    last_pos = pos
                    last_player = 1
            else:  # placing in opponent side
                if pos <= 5:  # in opponent houses
                    opponent[pos] += 1
                    last_pos = pos
                    last_player = 1
                else:  # switch back to your side, skip opponent store
                    player = 0
                    pos = 0
                    you[pos] += 1
                    last_pos = pos
                    last_player = 0
            pos += 1
        
        # Check for extra turn
        if last_player == 0 and last_pos == 6:
            extra_turn = True
        
        # Check for capture
        if (last_player == 0 and 0 <= last_pos <= 5 and 
            you[last_pos] == 1 and opponent[5 - last_pos] > 0):
            # Capture
            captured = opponent[5 - last_pos]
            you[6] += captured + 1
            you[last_pos] = 0
            opponent[5 - last_pos] = 0
        
        return you, opponent, extra_turn
    
    def evaluate_position(you_state, opp_state):
        """Evaluate a position from our perspective"""
        score = you_state[6] - opp_state[6]  # Store difference
        
        # Add value for seeds on our side (potential future points)
        our_seeds = sum(you_state[:6])
        opp_seeds = sum(opp_state[:6])
        
        # If game would end, calculate final scores
        if our_seeds == 0:
            final_you = you_state[6]
            final_opp = opp_state[6] + opp_seeds
            return final_you - final_opp
        elif opp_seeds == 0:
            final_you = you_state[6] + our_seeds
            final_opp = opp_state[6]
            return final_you - final_opp
        
        # Bonus for having more seeds on our side
        score += (our_seeds - opp_seeds) * 0.3
        
        # Small bonus for having seeds in houses that can reach our store
        for i in range(6):
            if you_state[i] == 6 - i:  # Exact amount to reach store
                score += 2
            elif you_state[i] > 0:
                # Bonus for potential captures
                if you_state[i] == (6 - i) + 7:  # Would land in empty house after going around
                    for j in range(6):
                        if you_state[j] == 0 and opp_state[5-j] > 0:
                            if you_state[i] == (6 - i) + 7 + j:
                                score += opp_state[5-j] * 0.5
        
        return score
    
    def minimax(you_state, opp_state, depth, is_our_turn, alpha, beta):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return evaluate_position(you_state, opp_state)
        
        if is_our_turn:
            max_eval = float('-inf')
            legal_moves = [i for i in range(6) if you_state[i] > 0]
            if not legal_moves:
                # Game over, opponent gets remaining seeds
                final_you = you_state[6]
                final_opp = opp_state[6] + sum(opp_state[:6])
                return final_you - final_opp
            
            for move in legal_moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                if extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            legal_moves = [i for i in range(6) if opp_state[i] > 0]
            if not legal_moves:
                # Game over, we get remaining seeds
                final_you = you_state[6] + sum(you_state[:6])
                final_opp = opp_state[6]
                return final_you - final_opp
            
            for move in legal_moves:
                new_opp, new_you, extra_turn = simulate_move(opp_state, you_state, move)
                if extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Try each legal move
    for move in legal_moves:
        new_you, new_opp, extra_turn = simulate_move(you, opponent, move)
        
        # Use minimax with limited depth
        if extra_turn:
            score = minimax(new_you, new_opp, 3, True, float('-inf'), float('inf'))
        else:
            score = minimax(new_you, new_opp, 3, False, float('-inf'), float('inf'))
        
        # Bonus for extra turns
        if extra_turn:
            score += 1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
