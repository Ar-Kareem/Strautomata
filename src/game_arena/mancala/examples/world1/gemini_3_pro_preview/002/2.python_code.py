
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy.
    Implements Iterative Deepening Negamax with Alpha-Beta pruning.
    """
    start_time = time.time()
    TIME_LIMIT = 0.92  # Safety buffer within 1.0s

    # Identify legal moves
    legal_moves = [i for i, x in enumerate(you[:6]) if x > 0]
    
    # If no choice or only one choice, return immediately
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Convert to immutable tuples for simulation efficiency
    state_you = tuple(you)
    state_opp = tuple(opponent)

    # Simulation function: returns (new_my, new_opp, is_extra_turn, is_game_over)
    def do_move(my_pits_t, opp_pits_t, move_idx):
        # Use lists for mutation
        my_pits = list(my_pits_t)
        opp_pits = list(opp_pits_t)
        
        seeds = my_pits[move_idx]
        my_pits[move_idx] = 0
        
        pos = move_idx
        while seeds > 0:
            pos += 1
            # Skip index 13 (virtual opponent store)
            if pos == 13:
                pos = 0
            
            # Distribute
            if pos < 6:
                my_pits[pos] += 1
            elif pos == 6:
                my_pits[6] += 1
            elif pos <= 12:
                # Map 7-12 to opponent's 0-5
                opp_pits[pos - 7] += 1
            
            seeds -= 1
        
        # Check rules based on where last seed landed (pos)
        extra_turn = False
        
        if pos == 6:
            extra_turn = True
        elif pos < 6 and my_pits[pos] == 1:
            # Capture Rule: Last seed in empty own house, opponent opposite is not empty
            opp_idx = 5 - pos
            if opp_pits[opp_idx] > 0:
                captured = 1 + opp_pits[opp_idx]
                my_pits[pos] = 0
                opp_pits[opp_idx] = 0
                my_pits[6] += captured
        
        # Game Over Check
        # If either side is empty, game ends immediately.
        my_empty = (sum(my_pits[:6]) == 0)
        opp_empty = (sum(opp_pits[:6]) == 0)
        
        is_over = False
        if my_empty or opp_empty:
            is_over = True
            extra_turn = False
            # Clean up: move all remainders to stores
            my_rem = sum(my_pits[:6])
            my_pits[6] += my_rem
            for i in range(6): my_pits[i] = 0
            
            opp_rem = sum(opp_pits[:6])
            opp_pits[6] += opp_rem
            for i in range(6): opp_pits[i] = 0
            
        return tuple(my_pits), tuple(opp_pits), extra_turn, is_over

    # Node counter for periodic time checks
    nodes_visited = 0

    def negamax(c_you, c_opp, depth, alpha, beta):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Check time every 1024 nodes to reduce overhead
        if nodes_visited & 1023 == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise TimeoutError

        # Heuristic / Base Case
        if depth <= 0:
            # Score: (My Store - Opp Store) weighted
            # Secondary: (My Side - Opp Side) - material on board
            return (c_you[6] - c_opp[6]) * 2 + (sum(c_you[:6]) - sum(c_opp[:6]))
        
        # Generate Moves
        moves = [i for i, x in enumerate(c_you[:6]) if x > 0]
        if not moves:
            # Should be covered by game over logic, but strictly:
            return (c_you[6] - c_opp[6]) * 100

        # Move Ordering: Prioritize moves that give extra turns or large swings
        candidates = []
        for m in moves:
            nm, no, ex, go = do_move(c_you, c_opp, m)
            # Simple sorting metric: resulting store diff
            val_est = nm[6] - no[6] 
            if go: val_est += 1000 # Prioritize winning
            if ex: val_est += 50   # Prioritize extra turns
            candidates.append((val_est, m, nm, no, ex, go))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        best_val = -float('inf')
        
        for _, m, next_you, next_opp, is_extra, is_over in candidates:
            if is_over:
                # Exact score, heavily weighted to ensure we pick winning paths
                val = (next_you[6] - next_opp[6]) * 1000
            elif is_extra:
                # Continue with same player, same depth (or decrement if strict on depth)
                # Using same depth allows exploring the chain fully
                val = negamax(next_you, next_opp, depth, alpha, beta)
            else:
                # Swap roles
                val = -negamax(next_opp, next_you, depth - 1, -beta, -alpha)
            
            if val > best_val:
                best_val = val
            
            alpha = max(alpha, val)
            if alpha >= beta:
                break
                
        return best_val

    # Main Iterative Deepening Loop
    best_move = legal_moves[0]
    
    # Pre-calculate root moves for ordering
    root_candidates = []
    for m in legal_moves:
        nm, no, ex, go = do_move(state_you, state_opp, m)
        est = nm[6] - no[6]
        if ex: est += 50
        root_candidates.append((est, m, nm, no, ex, go))
    # Sort
    root_candidates.sort(key=lambda x: x[0], reverse=True)
    
    try:
        # Increase depth until time runs out
        # Depth 20 is usually unreachable within 1s, serving as effective infinity
        for d in range(1, 40):
            current_depth_best = -1
            max_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            
            for _, m, next_you, next_opp, is_extra, is_over in root_candidates:
                if is_over:
                    val = (next_you[6] - next_opp[6]) * 1000
                elif is_extra:
                    val = negamax(next_you, next_opp, d, alpha, beta)
                else:
                    val = -negamax(next_opp, next_you, d - 1, -beta, -alpha)
                
                if val > max_val:
                    max_val = val
                    current_depth_best = m
                
                alpha = max(alpha, val)
                
                # Check time at root level too
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError
            
            # Update best move if we completed the depth
            best_move = current_depth_best

    except TimeoutError:
        # Time runs out, return best move from last fully searched depth
        pass
        
    return best_move
