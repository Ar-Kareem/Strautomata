
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        """Simulate a move and return the resulting state and whether we get an extra turn."""
        you_copy = you_state[:]
        opp_copy = opp_state[:]
        
        seeds = you_copy[move]
        you_copy[move] = 0
        
        pos = move
        player = 0  # 0 = us, 1 = opponent
        
        # Distribute seeds
        for _ in range(seeds):
            pos += 1
            
            if player == 0:  # Our side
                if pos <= 5:  # Our houses
                    you_copy[pos] += 1
                elif pos == 6:  # Our store
                    you_copy[6] += 1
                else:  # Switch to opponent side
                    player = 1
                    pos = 0
                    opp_copy[0] += 1
            else:  # Opponent side
                if pos <= 5:  # Opponent houses
                    opp_copy[pos] += 1
                else:  # Switch back to our side (skip opponent store)
                    player = 0
                    pos = 0
                    you_copy[0] += 1
        
        # Check for extra move
        extra_turn = (player == 0 and pos == 6)
        
        # Check for capture
        if (player == 0 and 0 <= pos <= 5 and 
            you_copy[pos] == 1 and opp_copy[5 - pos] > 0):
            # Capture
            captured = you_copy[pos] + opp_copy[5 - pos]
            you_copy[6] += captured
            you_copy[pos] = 0
            opp_copy[5 - pos] = 0
        
        return you_copy, opp_copy, extra_turn
    
    def evaluate_position(you_state, opp_state):
        """Evaluate the position from our perspective."""
        # Basic evaluation: store difference + position value
        store_diff = you_state[6] - opp_state[6]
        
        # Bonus for seeds on our side (potential future captures)
        our_seeds = sum(you_state[:6])
        opp_seeds = sum(opp_state[:6])
        
        # Bonus for having moves available
        our_moves = sum(1 for i in range(6) if you_state[i] > 0)
        opp_moves = sum(1 for i in range(6) if opp_state[i] > 0)
        
        # Check for game end
        if our_moves == 0:
            # Game ends, opponent gets remaining seeds
            final_our_score = you_state[6]
            final_opp_score = opp_state[6] + opp_seeds
            return final_our_score - final_opp_score
        elif opp_moves == 0:
            # Game ends, we get remaining seeds
            final_our_score = you_state[6] + our_seeds
            final_opp_score = opp_state[6]
            return final_our_score - final_opp_score
        
        # Position evaluation
        score = store_diff * 10
        score += (our_seeds - opp_seeds) * 0.5
        score += (our_moves - opp_moves) * 2
        
        # Bonus for seeds in houses that can reach our store
        for i in range(6):
            if you_state[i] > 0:
                steps_to_store = 6 - i
                if you_state[i] == steps_to_store:
                    score += 5  # Bonus for potential extra turn
        
        # Bonus for potential captures
        for i in range(6):
            if you_state[i] == 0 and opp_state[5 - i] > 0:
                # Empty house opposite to opponent seeds - good for captures
                reachable = False
                for j in range(6):
                    if you_state[j] > 0:
                        steps = you_state[j]
                        pos = j
                        # Simplified check if we can reach house i
                        if (pos + steps - 1) % 13 == i:
                            reachable = True
                            break
                if reachable:
                    score += opp_state[5 - i] * 0.3
        
        return score
    
    def minimax(you_state, opp_state, depth, maximizing, alpha, beta):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate_position(you_state, opp_state), -1
        
        if maximizing:
            max_eval = float('-inf')
            best_move = -1
            
            for move in range(6):
                if you_state[move] > 0:
                    new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                    
                    if extra_turn:
                        # We get another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
                    else:
                        # Opponent's turn
                        eval_score, _ = minimax(new_opp, new_you, depth - 1, False, alpha, beta)
                        eval_score = -eval_score  # Flip perspective
                    
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = move
                    
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = -1
            
            for move in range(6):
                if you_state[move] > 0:  # you_state is opponent from their perspective
                    new_you, new_opp, extra_turn = simulate_move(you_state, opp_state, move)
                    
                    if extra_turn:
                        # Opponent gets another turn
                        eval_score, _ = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
                    else:
                        # Our turn (flip back)
                        eval_score, _ = minimax(new_opp, new_you, depth - 1, True, alpha, beta)
                        eval_score = -eval_score  # Flip perspective
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            
            return min_eval, best_move
    
    # Try different depths based on game complexity
    total_seeds = sum(you) + sum(opponent)
    if total_seeds > 40:
        depth = 6
    elif total_seeds > 20:
        depth = 8
    else:
        depth = 10
    
    _, best_move = minimax(you, opponent, depth, True, float('-inf'), float('inf'))
    
    # Fallback to a simple heuristic if something goes wrong
    if best_move == -1:
        # Prefer moves that give extra turns
        for i in range(6):
            if you[i] > 0 and you[i] == 6 - i:
                return i
        
        # Otherwise, pick the house with most seeds
        best_move = 0
        for i in range(6):
            if you[i] > you[best_move]:
                best_move = i
    
    return best_move
