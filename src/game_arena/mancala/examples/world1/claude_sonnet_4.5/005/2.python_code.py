
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opponent, move):
        """Simulate a move and return (new_you, new_opponent, extra_turn)"""
        you = you[:]
        opponent = opponent[:]
        
        seeds = you[move]
        you[move] = 0
        
        pos = move
        on_you_side = True
        
        while seeds > 0:
            pos += 1
            
            if on_you_side:
                if pos <= 6:
                    you[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        if pos == 6:
                            return you, opponent, True
                        elif you[pos] == 1 and opponent[5 - pos] > 0:
                            # Capture
                            you[6] += you[pos] + opponent[5 - pos]
                            you[pos] = 0
                            opponent[5 - pos] = 0
                else:
                    on_you_side = False
                    pos = -1
            else:
                if pos <= 5:
                    opponent[pos] += 1
                    seeds -= 1
                else:
                    on_you_side = True
                    pos = -1
        
        return you, opponent, False
    
    def is_game_over(you, opponent):
        return sum(you[:6]) == 0 or sum(opponent[:6]) == 0
    
    def final_score(you, opponent):
        """Calculate final score difference (you - opponent)"""
        you_total = you[6] + sum(you[:6])
        opp_total = opponent[6] + sum(opponent[:6])
        return you_total - opp_total
    
    def minimax(you, opponent, depth, alpha, beta, is_you_turn):
        if depth == 0 or is_game_over(you, opponent):
            if is_game_over(you, opponent):
                return final_score(you, opponent)
            return you[6] - opponent[6]
        
        legal_moves = [i for i in range(6) if you[i] > 0]
        if not legal_moves:
            return final_score(you, opponent)
        
        if is_you_turn:
            max_eval = float('-inf')
            for move in legal_moves:
                new_you, new_opp, extra = simulate_move(you, opponent, move)
                if extra:
                    score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
                    score = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_you, new_opp, extra = simulate_move(you, opponent, move)
                if extra:
                    score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    # Score from original you's perspective (negated)
                    score = -minimax(new_you, new_opp, depth - 1, -beta, -alpha, True)
                min_eval = min(min_eval, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_eval
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra = simulate_move(you, opponent, move)
        if extra:
            score = minimax(new_you, new_opp, 7, float('-inf'), float('inf'), True)
        else:
            score = minimax(new_opp, new_you, 7, float('-inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
