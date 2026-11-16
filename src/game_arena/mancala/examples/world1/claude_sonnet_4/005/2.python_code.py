
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    
    def simulate_move(you_state, opp_state, house):
        """Simulate a move and return new state and whether player gets extra turn"""
        you = you_state.copy()
        opponent = opp_state.copy()
        seeds = you[house]
        you[house] = 0
        
        if seeds == 0:
            return you, opponent, False
        
        # Track position for seed distribution
        current_side = 'you'
        current_idx = house
        last_side = None
        last_idx = None
        
        for _ in range(seeds):
            # Move to next position
            if current_side == 'you':
                current_idx += 1
                if current_idx == 6:  # My store
                    you[6] += 1
                    last_side, last_idx = 'you', 6
                    # Next goes to opponent[0]
                    current_side = 'opp'
                    current_idx = 0
                elif current_idx < 6:  # My houses
                    you[current_idx] += 1
                    last_side, last_idx = 'you', current_idx
                else:  # Wrap to opponent side
                    current_side = 'opp'
                    current_idx = 0
                    opponent[current_idx] += 1
                    last_side, last_idx = 'opp', current_idx
                    current_idx += 1
            else:  # current_side == 'opp'
                if current_idx <= 5:  # Opponent houses
                    opponent[current_idx] += 1
                    last_side, last_idx = 'opp', current_idx
                    current_idx += 1
                    if current_idx > 5:  # Wrap to my side
                        current_side = 'you'
                        current_idx = 0
        
        # Check for extra turn
        extra_turn = (last_side == 'you' and last_idx == 6)
        
        # Check for capture
        if last_side == 'you' and last_idx < 6:  # Landed in my house
            if you[last_idx] == 1:  # Was empty before this seed
                opposite_idx = 5 - last_idx
                if opponent[opposite_idx] > 0:
                    # Capture!
                    you[6] += 1 + opponent[opposite_idx]
                    you[last_idx] = 0
                    opponent[opposite_idx] = 0
        
        return you, opponent, extra_turn
    
    def is_terminal(you_state, opp_state):
        """Check if game is over"""
        you_empty = all(you_state[i] == 0 for i in range(6))
        opp_empty = all(opp_state[i] == 0 for i in range(6))
        return you_empty or opp_empty
    
    def get_final_score(you_state, opp_state):
        """Get final scores assuming game ends now"""
        you_final = you_state.copy()
        opp_final = opp_state.copy()
        
        # Move remaining seeds to stores
        you_final[6] += sum(you_final[:6])
        opp_final[6] += sum(opp_final[:6])
        
        return you_final[6] - opp_final[6]
    
    def evaluate(you_state, opp_state):
        """Evaluate position from my perspective"""
        if is_terminal(you_state, opp_state):
            return get_final_score(you_state, opp_state)
        
        # Heuristic: store difference + small bonus for seeds on my side
        store_diff = you_state[6] - opp_state[6]
        my_seeds = sum(you_state[:6])
        opp_seeds = sum(opp_state[:6])
        seed_advantage = (my_seeds - opp_seeds) * 0.1
        
        return store_diff + seed_advantage
    
    def get_legal_moves(player_state):
        """Get all legal moves for a player"""
        return [i for i in range(6) if player_state[i] > 0]
    
    def minimax(you_state, opp_state, depth, alpha, beta, maximizing, start_time):
        """Minimax with alpha-beta pruning"""
        if time.time() - start_time > 0.8:  # Time limit
            return evaluate(you_state, opp_state), -1
            
        if depth == 0 or is_terminal(you_state, opp_state):
            return evaluate(you_state, opp_state), -1
        
        if maximizing:
            max_eval = float('-inf')
            best_move = -1
            moves = get_legal_moves(you_state)
            
            # Prioritize moves that might give extra turns
            def move_priority(move):
                seeds = you_state[move]
                lands_in_store = (move + seeds) % 13 == 6
                return -int(lands_in_store)  # Negative for better priority
            
            moves.sort(key=move_priority)
            
            for move in moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    # I get another turn
                    eval_score, _ = minimax(new_you, new_opp, depth-1, alpha, beta, True, start_time)
                else:
                    # Opponent's turn
                    eval_score, _ = minimax(new_opp, new_you, depth-1, alpha, beta, False, start_time)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            # Minimizing (opponent's turn) - note swapped you/opp perspective
            min_eval = float('inf')
            best_move = -1
            moves = get_legal_moves(you_state)  # you_state is actually opponent from original perspective
            
            for move in moves:
                new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                
                if extra_turn:
                    # Opponent gets another turn
                    eval_score, _ = minimax(new_you, new_opp, depth-1, alpha, beta, False, start_time)
                else:
                    # Back to my turn (swap back)
                    eval_score, _ = minimax(new_opp, new_you, depth-1, alpha, beta, True, start_time)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Main decision logic
    start_time = time.time()
    legal_moves = get_legal_moves(you)
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Try increasing depths until time runs out
    for depth in range(1, 15):
        if time.time() - start_time > 0.7:
            break
            
        score, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True, start_time)
        
        if move != -1:
            best_move = move
            best_score = score
    
    return best_move
