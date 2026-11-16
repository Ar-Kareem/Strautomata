
import time

def policy(me, opp, color):
    # Game constants
    BOARD_SIZE = 8
    INF = float('inf')
    TIME_LIMIT = 0.95 # seconds

    # Convert lists to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)

    # Determine directions and goals based on color
    # 'w' moves upwards (increasing row), home row 0, goal row 7
    # 'b' moves downwards (decreasing row), home row 7, goal row 0
    if color == 'w':
        my_dir = 1
        my_goal_row = 7
        opp_goal_row = 0
        opp_color = 'b'
    else:
        my_dir = -1
        my_goal_row = 0
        opp_goal_row = 7
        opp_color = 'w'

    # Precompute values for heuristic
    # Distance from my goal to my piece (how far I've traveled)
    # For white (0->7), row index is distance. For black (7->0), 7-row is distance.
    def get_advancement(r, is_me):
        if is_me:
            return r if color == 'w' else (7 - r)
        else:
            return (7 - r) if color == 'w' else r

    # Heuristic evaluation function
    def evaluate():
        # Check for immediate wins/losses handled in search, 
        # but evaluate material and position here.
        score = 0
        
        # My pieces
        for r, c in me_set:
            score += 10000 # Base value for material
            
            # Advancement bonus (stronger as pieces get closer)
            # 0 to 7 steps.
            dist = get_advancement(r, True)
            score += (dist ** 2) * 20 
            
            # Positional bonus: Center control
            if 2 <= c <= 5:
                score += 50
            if 3 <= c <= 4:
                score += 50
                
            # Winning threat/position
            if (color == 'w' and r == 7) or (color == 'b' and r == 0):
                score += 100000 # Should be caught by win check, but safety
                
            # Threatening opponent? (Can capture)
            # Check diagonal forward
            for dc in [-1, 1]:
                tr, tc = r + my_dir, c + dc
                if 0 <= tc < BOARD_SIZE and (tr, tc) in opp_set:
                    score += 500 # Threat bonus

        # Opponent pieces
        for r, c in opp_set:
            score -= 10000
            
            # Opponent advancement
            opp_dist = get_advancement(r, False)
            # If opponent is 'w', their advancement is r. If 'b', 7-r.
            # We want to penalize their advancement.
            score -= (opp_dist ** 2) * 25 # Penalize their progress slightly more
            
            if 2 <= c <= 5:
                score -= 50
            if 3 <= c <= 4:
                score -= 50

            if (color == 'w' and r == 0) or (color == 'b' and r == 7):
                score -= 100000
                
        return score

    # Generator for legal moves
    # Returns (score_estimate, from_pos, to_pos, captured_pos)
    # score_estimate is for move ordering
    def get_moves(pieces, target_set, direction, is_maximizing):
        moves = []
        for r, c in pieces:
            # Straight forward
            fr, fc = r + direction, c
            if 0 <= fr < BOARD_SIZE and (fr, fc) not in target_set and (fr, fc) not in (me_set if is_maximizing else opp_set):
                # Heuristic: prioritize forward movement
                # Calculate advancement delta
                adv = 1
                # Check if winning move
                win_bonus = 0
                if (is_maximizing and fr == my_goal_row) or (not is_maximizing and fr == opp_goal_row):
                    win_bonus = 1000000
                
                moves.append((win_bonus + adv * 100, (r, c), (fr, fc), None))

            # Diagonals
            for dc in [-1, 1]:
                fr, fc = r + direction, c + dc
                if 0 <= fr < BOARD_SIZE and 0 <= fc < BOARD_SIZE:
                    is_capture = (fr, fc) in target_set
                    is_empty = (fr, fc) not in target_set and (fr, fc) not in (me_set if is_maximizing else opp_set)
                    
                    if is_capture:
                        # Prioritize captures
                        # Calculate advancement delta
                        adv = 1
                        win_bonus = 0
                        if (is_maximizing and fr == my_goal_row) or (not is_maximizing and fr == opp_goal_row):
                            win_bonus = 1000000
                        moves.append((win_bonus + 10000 + adv * 100, (r, c), (fr, fc), (fr, fc)))
                    elif is_empty:
                        # Diagonal empty move
                        adv = 1
                        win_bonus = 0
                        if (is_maximizing and fr == my_goal_row) or (not is_maximizing and fr == opp_goal_row):
                            win_bonus = 1000000
                        moves.append((win_bonus + adv * 100, (r, c), (fr, fc), None))
        
        # Sort moves descending by estimate to improve pruning
        moves.sort(key=lambda x: x[0], reverse=True)
        return moves

    # Minimax with Alpha-Beta Pruning
    def minimax(depth, alpha, beta, is_maximizing):
        # Check win/loss conditions
        # Did I reach goal?
        for r, c in me_set:
            if r == my_goal_row:
                return INF - 1
        # Did Opp reach goal?
        for r, c in opp_set:
            if r == opp_goal_row:
                return -INF + 1
        
        if depth == 0:
            return evaluate()

        if is_maximizing:
            max_eval = -INF
            moves = get_moves(me_set, opp_set, my_dir, True)
            
            if not moves:
                return -INF + 10 # No moves left = loss

            for _, f, t, cap in moves:
                # Apply move
                me_set.remove(f)
                me_set.add(t)
                if cap:
                    opp_set.remove(cap)
                
                eval_val = minimax(depth - 1, alpha, beta, False)
                
                # Undo move
                me_set.add(f)
                me_set.remove(t)
                if cap:
                    opp_set.add(cap)
                
                if eval_val > max_eval:
                    max_eval = eval_val
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            moves = get_moves(opp_set, me_set, -my_dir, False)
            
            if not moves:
                return INF - 10 # Opponent no moves = win for me

            for _, f, t, cap in moves:
                # Apply move
                opp_set.remove(f)
                opp_set.add(t)
                if cap:
                    me_set.remove(cap)
                
                eval_val = minimax(depth - 1, alpha, beta, True)
                
                # Undo move
                opp_set.add(f)
                opp_set.remove(t)
                if cap:
                    me_set.add(cap)
                
                if eval_val < min_eval:
                    min_eval = eval_val
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Iterative Deepening Loop
    start_time = time.time()
    best_move = None
    
    # Initial depth
    depth = 1
    
    # Find at least one move immediately (depth 1)
    # Always maximize first
    moves = get_moves(me_set, opp_set, my_dir, True)
    if moves:
        best_move = (moves[0][1], moves[0][2])

    while True:
        current_time = time.time()
        if current_time - start_time > TIME_LIMIT * 0.8: # safety margin
            break
            
        current_best = None
        max_eval = -INF
        
        # Get ordered moves for root
        # We re-fetch moves inside loop because board state doesn't change in root, 
        # but 'get_moves' sorts them, which is fine.
        # To save time, we can cache the sorted move list for the root? 
        # No, we need to re-evaluate minimax for them.
        
        root_moves = get_moves(me_set, opp_set, my_dir, True)
        
        # We need to search all moves at root to find the best one
        alpha = -INF
        beta = INF
        
        for _, f, t, cap in root_moves:
            # Check time before each branch at root to ensure we don't hang
            if time.time() - start_time > TIME_LIMIT:
                break
                
            # Apply
            me_set.remove(f)
            me_set.add(t)
            if cap:
                opp_set.remove(cap)
            
            score = minimax(depth - 1, alpha, beta, False)
            
            # Undo
            me_set.add(f)
            me_set.remove(t)
            if cap:
                opp_set.add(cap)
            
            if score > max_eval:
                max_eval = score
                current_best = (f, t)
            
            alpha = max(alpha, score)
            
        # If we finished searching this depth without timeout for the whole loop
        if current_best:
            best_move = current_best
        else:
            # If we broke early due to time, use the best found so far (previous depth)
            break
            
        depth += 1
        
        # Safety break for very long searches (though time check handles it)
        if depth > 10:
            break

    return best_move
