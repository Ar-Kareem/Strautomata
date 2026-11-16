
import time

def policy(me, opp, color):
    start_time = time.time()
    
    # Convert lists to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Define directions and goals based on color
    # White moves UP (increasing row index), Black moves DOWN (decreasing row index)
    if color == 'w':
        my_dir = 1
        my_goal_row = 7
        opp_dir = -1
        opp_goal_row = 0
    else:
        my_dir = -1
        my_goal_row = 0
        opp_dir = 1
        opp_goal_row = 7

    # Helper to generate all legal moves for a player
    # pieces: set of (r, c) for the player to move
    # direction: +1 or -1
    # opp_pieces: set of (r, c) for the opponent
    def get_moves(pieces, direction, opp_pieces):
        moves = []
        occupied = pieces | opp_pieces
        for r, c in pieces:
            nr = r + direction
            # Check row bounds implied by game rules (pieces shouldn't exceed board, 
            # but direction might push them off board if we don't check win condition first)
            # However, here we just generate moves. 
            # If a piece is on the goal row, the game is over, so we assume pieces are not on goal row yet.
            if not (0 <= nr <= 7):
                continue
                
            # Straight move
            if (nr, c) not in occupied:
                moves.append(((r, c), (nr, c), False)) # False = no capture
                
            # Diagonal moves
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc <= 7:
                    target = (nr, nc)
                    # Capture move
                    if target in opp_pieces:
                        moves.append(((r, c), target, True))
                    # Diagonal step to empty square
                    elif target not in occupied:
                        moves.append(((r, c), target, False))
        return moves

    # Heuristic evaluation function
    def evaluate(my_pieces, opp_pieces):
        score = 0
        # 1. Material
        my_count = len(my_pieces)
        opp_count = len(opp_pieces)
        score += (my_count - opp_count) * 1000
        
        # 2. Advancement and Win Threats
        # My pieces
        for r, c in my_pieces:
            if my_dir == 1: # White
                dist = my_goal_row - r
                score += (7 - dist) * 10
                if r == 6: score += 500 # Very close to winning
                if r == 7: score += 100000 # Should be caught by terminal check, but safe
            else: # Black
                dist = r - my_goal_row
                score += (7 - dist) * 10
                if r == 1: score += 500
                if r == 0: score += 100000

        # Opponent pieces
        for r, c in opp_pieces:
            if opp_dir == 1: # Opponent is White
                dist = opp_goal_row - r # Opponent goal is their destination (7)
                # Actually opponent dist to my home row (0) is r - 0 = r.
                # Opponent goal row is 7 (if W) or 0 (if B).
                # Dist from opponent piece to opponent goal:
                opp_dist = abs(opp_goal_row - r)
                score -= (7 - opp_dist) * 10
                if r == 6: score -= 500
            else: # Opponent is Black
                opp_dist = abs(opp_goal_row - r)
                score -= (7 - opp_dist) * 10
                if r == 1: score -= 500
                
        return score

    # Move ordering for Alpha-Beta pruning efficiency
    def order_moves(moves, goal_row):
        def score_move(m):
            fr, to, cap = m
            val = 0
            if to[0] == goal_row: val += 100000 # Win
            if cap: val += 100 # Capture
            # Advancement
            val += abs(to[0] - fr[0]) * 10
            return val
        moves.sort(key=score_move, reverse=True)

    # Alpha-Beta Minimax with iterative deepening
    best_move = None
    
    # We assume we always have moves if game is not over
    # Initial move ordering for root
    initial_moves = get_moves(me_set, my_dir, opp_set)
    order_moves(initial_moves, my_goal_row)
    if not initial_moves:
        return None # Game over, should not happen if called
    best_move = (initial_moves[0][0], initial_moves[0][1])

    def minimax(my_p, opp_p, depth, alpha, beta, is_max):
        # Time check
        if time.time() - start_time > 0.95:
            return 0, None, True # Timeout

        # Terminal condition: Someone reached goal?
        # Since state comes from valid moves, checking goal row is enough
        if is_max:
            for r, c in my_p:
                if r == my_goal_row: return 100000, None, False
            for r, c in opp_p:
                if r == opp_goal_row: return -100000, None, False
        else:
            for r, c in opp_p:
                if r == opp_goal_row: return -100000, None, False
            for r, c in my_p:
                if r == my_goal_row: return 100000, None, False

        if depth == 0:
            return evaluate(my_p, opp_p), None, False

        if is_max:
            moves = get_moves(my_p, my_dir, opp_p)
            if not moves: return -100000, None, False # Stuck
            order_moves(moves, my_goal_row)
            
            max_eval = float('-inf')
            best_m = None
            for fr, to, cap in moves:
                new_my = set(my_p)
                new_opp = set(opp_p)
                new_my.remove(fr)
                new_my.add(to)
                if cap:
                    new_opp.remove(to)
                
                eval_val, _, timeout = minimax(new_my, new_opp, depth-1, alpha, beta, False)
                if timeout: return 0, None, True
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_m = (fr, to)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_m, False
        else:
            moves = get_moves(opp_p, opp_dir, my_p)
            if not moves: return 100000, None, False # Opponent stuck
            # Order for opponent (moves that are good for them, bad for me)
            # Opponent wants to reach opp_goal_row
            order_moves(moves, opp_goal_row)
            
            min_eval = float('inf')
            best_m = None
            for fr, to, cap in moves:
                new_my = set(my_p)
                new_opp = set(opp_p)
                new_opp.remove(fr)
                new_opp.add(to)
                if cap:
                    new_my.remove(to)
                
                eval_val, _, timeout = minimax(new_my, new_opp, depth-1, alpha, beta, True)
                if timeout: return 0, None, True
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_m = (fr, to)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_m, False

    # Iterative Deepening Loop
    for depth in range(1, 20):
        val, move, timeout = minimax(me_set, opp_set, depth, float('-inf'), float('inf'), True)
        if timeout:
            break
        if move:
            best_move = move
        # If we found a sure win, stop
        if val > 50000:
            break
        if time.time() - start_time > 0.8:
            break

    return best_move
