
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate(player_pits, opponent_pits, move):
        """Simulate a move. Returns (new_player_pits, new_opponent_pits, extra_turn)"""
        player_pits = player_pits[:]
        opponent_pits = opponent_pits[:]
        
        seeds = player_pits[move]
        player_pits[move] = 0
        pos = move
        
        while seeds > 0:
            pos += 1
            if pos < 6:
                player_pits[pos] += 1
                seeds -= 1
            elif pos == 6:
                player_pits[6] += 1
                seeds -= 1
            elif pos < 13:
                opponent_pits[pos - 7] += 1
                seeds -= 1
            else:
                pos = -1
        
        extra_turn = (pos == 6)
        
        # Capture: last seed in empty house on player's side
        if 0 <= pos < 6 and player_pits[pos] == 1:
            opp_idx = 5 - pos
            if opponent_pits[opp_idx] > 0:
                player_pits[6] += 1 + opponent_pits[opp_idx]
                player_pits[pos] = 0
                opponent_pits[opp_idx] = 0
        
        return player_pits, opponent_pits, extra_turn
    
    def game_over(my_pits, opp_pits):
        return sum(my_pits[:6]) == 0 or sum(opp_pits[:6]) == 0
    
    def final_score(my_pits, opp_pits):
        my_total = my_pits[6] + sum(my_pits[:6])
        opp_total = opp_pits[6] + sum(opp_pits[:6])
        return my_total - opp_total
    
    def evaluate(my_pits, opp_pits):
        # Heuristic: score difference plus small bonus for seeds on my side
        score = my_pits[6] - opp_pits[6]
        # Bonus for having more seeds available
        score += 0.1 * (sum(my_pits[:6]) - sum(opp_pits[:6]))
        return score
    
    def minimax(my_pits, opp_pits, depth, alpha, beta, is_my_turn):
        """
        Always evaluates from original 'my' perspective.
        my_pits/opp_pits are always from original my perspective.
        is_my_turn indicates whose turn it is.
        """
        if game_over(my_pits, opp_pits):
            return final_score(my_pits, opp_pits), None
        
        if depth == 0:
            return evaluate(my_pits, opp_pits), None
        
        if is_my_turn:
            if sum(my_pits[:6]) == 0:
                return final_score(my_pits, opp_pits), None
            best_score = float('-inf')
            best_move = None
            for m in range(6):
                if my_pits[m] > 0:
                    new_my, new_opp, extra = simulate(my_pits, opp_pits, m)
                    if extra:
                        score, _ = minimax(new_my, new_opp, depth, alpha, beta, True)
                    else:
                        score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                    if score > best_score:
                        best_score = score
                        best_move = m
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
            return best_score, best_move
        else:
            if sum(opp_pits[:6]) == 0:
                return final_score(my_pits, opp_pits), None
            best_score = float('inf')
            best_move = None
            for m in range(6):
                if opp_pits[m] > 0:
                    # Opponent makes move - simulate from their perspective
                    new_opp, new_my, extra = simulate(opp_pits, my_pits, m)
                    if extra:
                        score, _ = minimax(new_my, new_opp, depth, alpha, beta, False)
                    else:
                        score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                    if score < best_score:
                        best_score = score
                        best_move = m
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
            return best_score, best_move
    
    # Iterative deepening with time limit awareness
    import time
    start = time.time()
    best_move = None
    
    # Find any legal move as fallback
    for m in range(6):
        if you[m] > 0:
            best_move = m
            break
    
    # Try increasing depths
    for depth in range(1, 15):
        if time.time() - start > 0.8:
            break
        try:
            _, move = minimax(you[:], opponent[:], depth, float('-inf'), float('inf'), True)
            if move is not None:
                best_move = move
        except:
            break
        if time.time() - start > 0.8:
            break
    
    return best_move
