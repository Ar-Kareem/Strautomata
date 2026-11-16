
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opp, house):
        """Simulate a move and return (new_you, new_opp, extra_turn)"""
        you = you[:]
        opp = opp[:]
        
        if you[house] == 0:
            return None
        
        seeds = you[house]
        you[house] = 0
        
        # Create circular path: you[house+1..5], you[6], opp[0..5], you[0..5], ...
        # Skip opponent[6]
        positions = []
        pos_idx = house + 1
        
        while len(positions) < seeds:
            # Your houses and store
            for i in range(pos_idx, 7):
                positions.append(('you', i))
                if len(positions) == seeds:
                    break
            if len(positions) == seeds:
                break
            
            # Opponent houses (not store)
            for i in range(6):
                positions.append(('opp', i))
                if len(positions) == seeds:
                    break
            if len(positions) == seeds:
                break
            
            pos_idx = 0  # Start from beginning of your side
        
        # Distribute seeds
        for side, idx in positions:
            if side == 'you':
                you[idx] += 1
            else:
                opp[idx] += 1
        
        last_side, last_idx = positions[-1]
        
        # Check for extra turn
        extra_turn = (last_side == 'you' and last_idx == 6)
        
        # Check for capture
        if last_side == 'you' and 0 <= last_idx <= 5:
            if you[last_idx] == 1:  # Was empty before drop
                opposite = 5 - last_idx
                if opp[opposite] > 0:
                    you[6] += you[last_idx] + opp[opposite]
                    you[last_idx] = 0
                    opp[opposite] = 0
        
        return you, opp, extra_turn
    
    def is_terminal(you, opp):
        return sum(you[:6]) == 0 or sum(opp[:6]) == 0
    
    def evaluate(you, opp):
        """Evaluate board from 'you' perspective"""
        you_store = you[6]
        opp_store = opp[6]
        
        if sum(you[:6]) == 0:
            opp_store += sum(opp[:6])
        elif sum(opp[:6]) == 0:
            you_store += sum(you[:6])
        
        return you_store - opp_store + sum(you[:6]) * 0.05
    
    def minimax(you, opp, depth, alpha, beta, maximizing):
        if depth == 0 or is_terminal(you, opp):
            return evaluate(you, opp), None
        
        legal_moves = [i for i in range(6) if you[i] > 0]
        if not legal_moves:
            return evaluate(you, opp), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = legal_moves[0]
            
            for move in legal_moves:
                result = simulate_move(you, opp, move)
                if result is None:
                    continue
                new_you, new_opp, extra_turn = result
                
                if extra_turn:
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
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
            best_move = legal_moves[0]
            
            for move in legal_moves:
                result = simulate_move(you, opp, move)
                if result is None:
                    continue
                new_you, new_opp, extra_turn = result
                
                if extra_turn:
                    eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    eval_score, _ = minimax(new_opp, new_you, depth - 1, alpha, beta, True)
                    eval_score = -eval_score
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    _, best_move = minimax(you, opponent, depth=10, alpha=float('-inf'), beta=float('inf'), maximizing=True)
    
    if best_move is None:
        legal_moves = [i for i in range(6) if you[i] > 0]
        best_move = legal_moves[0]
    
    return best_move
