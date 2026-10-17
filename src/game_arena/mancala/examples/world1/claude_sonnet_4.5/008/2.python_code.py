
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opp, move):
        """
        Simulate a move and return (new_you, new_opp, extra_turn, game_over)
        """
        you = you[:]
        opp = opp[:]
        
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
        
        # Check for extra turn
        extra_turn = (side == 'you' and pos == 6)
        
        # Check for capture
        if not extra_turn and side == 'you' and 0 <= pos <= 5:
            if you[pos] == 1 and opp[5 - pos] > 0:  # Was empty before drop
                you[6] += you[pos] + opp[5 - pos]
                you[pos] = 0
                opp[5 - pos] = 0
        
        # Check game over
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
        
        return you, opp, extra_turn, game_over
    
    def evaluate(you, opp):
        """Evaluate position from 'you' perspective"""
        score = (you[6] - opp[6]) * 10
        you_seeds = sum(you[:6])
        opp_seeds = sum(opp[:6])
        score += (you_seeds - opp_seeds) * 0.5
        return score
    
    def get_legal_moves(player):
        return [i for i in range(6) if player[i] > 0]
    
    def minimax(you, opp, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(you, opp)
        
        legal_moves = get_legal_moves(you if maximizing else opp)
        
        if not legal_moves:
            you_copy = you[:]
            opp_copy = opp[:]
            for i in range(6):
                you_copy[6] += you_copy[i]
                you_copy[i] = 0
                opp_copy[6] += opp_copy[i]
                opp_copy[i] = 0
            return evaluate(you_copy, opp_copy)
        
        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                new_you, new_opp, extra_turn, game_over = simulate_move(you, opp, move)
                
                if game_over:
                    eval_score = evaluate(new_you, new_opp)
                elif extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
                    eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_opp, new_you, extra_turn, game_over = simulate_move(opp, you, move)
                
                if game_over:
                    eval_score = evaluate(new_you, new_opp)
                elif extra_turn:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    legal_moves = get_legal_moves(you)
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    depth = 10
    
    for move in legal_moves:
        new_you, new_opp, extra_turn, game_over = simulate_move(you, opponent, move)
        
        if game_over:
            score = evaluate(new_you, new_opp)
        elif extra_turn:
            score = minimax(new_you, new_opp, depth - 1, float('-inf'), float('inf'), True)
        else:
            score = minimax(new_opp, new_you, depth - 1, float('-inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
