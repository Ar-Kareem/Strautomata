
def policy(you: list[int], opponent: list[int]) -> int:
    import sys
    
    # Configuration
    MAX_DEPTH = 7
    INF = 10**9
    
    # Weights for heuristic evaluation: seeds closer to store are more valuable
    WEIGHTS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    
    def evaluate(p, o):
        """Evaluate board from perspective of p. Positive is good for p."""
        # Check terminal states
        if all(x == 0 for x in p[:6]):
            # p has no moves, o collects remaining seeds
            return p[6] - (o[6] + sum(o[:6]))
        if all(x == 0 for x in o[:6]):
            # o has no moves, p collects remaining seeds  
            return (p[6] + sum(p[:6])) - o[6]
        
        # Non-terminal: store difference + weighted house seeds
        score = p[6] - o[6]
        for i in range(6):
            score += WEIGHTS[i] * p[i]
            score -= WEIGHTS[i] * o[i]
        return score
    
    def apply_move(p, o, idx):
        """Apply move idx for player p. Returns (new_p, new_o, extra_turn)."""
        p = list(p)
        o = list(o)
        seeds = p[idx]
        p[idx] = 0
        pos = idx
        
        # Sow seeds
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == 13:  # Skip opponent's store
                continue
            if pos <= 5:
                p[pos] += 1
            elif pos == 6:
                p[6] += 1
            else:  # 7-12 map to opponent houses 0-5
                o[pos - 7] += 1
            seeds -= 1
        
        extra = (pos == 6)
        
        # Capture rule: landed in own empty house (0-5), opposite has seeds
        if not extra and 0 <= pos <= 5 and p[pos] == 1 and o[5 - pos] > 0:
            p[6] += 1 + o[5 - pos]
            p[pos] = 0
            o[5 - pos] = 0
        
        # Check game end conditions
        if all(x == 0 for x in p[:6]):
            # Opponent collects their seeds
            o[6] += sum(o[:6])
            for i in range(6):
                o[i] = 0
        elif all(x == 0 for x in o[:6]):
            # Current player collects their seeds
            p[6] += sum(p[:6])
            for i in range(6):
                p[i] = 0
                
        return p, o, extra
    
    def minimax(p, o, depth, alpha, beta, maximizing):
        """
        Minimax with alpha-beta pruning.
        p: player to move, o: opponent
        maximizing: True if p is the original player (we want to maximize)
        Returns score from perspective of original player.
        """
        # Terminal check
        if all(x == 0 for x in p[:6]) or all(x == 0 for x in o[:6]):
            val = evaluate(p, o)
            return val if maximizing else -val
        
        if depth == 0:
            val = evaluate(p, o)
            return val if maximizing else -val
        
        legal_moves = [i for i in range(6) if p[i] > 0]
        
        # Move ordering: prioritize extra turns, then captures, then higher indices
        def move_priority(idx):
            np, no, extra = apply_move(p, o, idx)
            if extra:
                return 3
            # Check if capture happened (p's store increased by more than 1 and last was in house)
            elif np[6] > p[6] + 1 and (np[idx] == 0 if idx <= 5 else False):
                return 2
            else:
                return 1
        
        legal_moves.sort(key=lambda x: (move_priority(x), x), reverse=True)
        
        if maximizing:
            max_eval = -INF
            for move in legal_moves:
                np, no, extra = apply_move(p, o, move)
                if extra:
                    eval_score = minimax(np, no, depth - 1, alpha, beta, True)
                else:
                    eval_score = minimax(no, np, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for move in legal_moves:
                np, no, extra = apply_move(p, o, move)
                if extra:
                    eval_score = minimax(np, no, depth - 1, alpha, beta, False)
                else:
                    eval_score = minimax(no, np, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get legal moves
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # Should not happen per problem statement
    if len(legal) == 1:
        return legal[0]
    
    best_move = legal[0]
    best_score = -INF
    
    # Order moves for root to ensure we have a good move even if time runs out
    def root_priority(idx):
        ny, no, extra = apply_move(you, opponent, idx)
        if extra:
            return (2, 0)
        # Simple capture detection
        if ny[6] > you[6] + 1:
            return (1, 0)
        return (0, you[idx])
    
    legal.sort(key=lambda x: root_priority(x), reverse=True)
    
    for move in legal:
        ny, no, extra = apply_move(you, opponent, move)
        if extra:
            score = minimax(ny, no, MAX_DEPTH - 1, -INF, INF, True)
        else:
            score = minimax(no, ny, MAX_DEPTH - 1, -INF, INF, False)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
