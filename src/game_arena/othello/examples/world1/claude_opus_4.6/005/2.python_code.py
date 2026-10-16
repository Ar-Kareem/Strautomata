
import numpy as np
import time

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start_time = time.time()
    
    def get_legal_moves(me, opp):
        moves = []
        for r in range(8):
            for c in range(8):
                if me[r][c] or opp[r][c]:
                    continue
                if is_legal(me, opp, r, c):
                    moves.append((r, c))
        return moves
    
    def is_legal(me, opp, r, c):
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            found_opp = False
            while 0 <= nr < 8 and 0 <= nc < 8:
                if opp[nr][nc]:
                    found_opp = True
                elif me[nr][nc]:
                    if found_opp:
                        return True
                    break
                else:
                    break
                nr += dr
                nc += dc
        return False
    
    def make_move(me, opp, r, c):
        new_me = me.copy()
        new_opp = opp.copy()
        new_me[r][c] = 1
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            to_flip = []
            while 0 <= nr < 8 and 0 <= nc < 8:
                if new_opp[nr][nc]:
                    to_flip.append((nr, nc))
                elif new_me[nr][nc]:
                    for fr, fc in to_flip:
                        new_opp[fr][fc] = 0
                        new_me[fr][fc] = 1
                    break
                else:
                    break
                nr += dr
                nc += dc
        return new_me, new_opp
    
    WEIGHTS = np.array([
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [ 10,  -5,   5,   3,   3,   5,  -5,  10],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [ 10,  -5,   5,   3,   3,   5,  -5,  10],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [100, -20,  10,   5,   5,  10, -20, 100],
    ], dtype=float)
    
    corners = [(0,0),(0,7),(7,0),(7,7)]
    
    def evaluate(me, opp):
        empty = 64 - np.sum(me) - np.sum(opp)
        my_count = np.sum(me)
        opp_count = np.sum(opp)
        
        # Endgame: pure disc count
        if empty == 0:
            diff = my_count - opp_count
            if diff > 0: return 10000 + diff
            elif diff < 0: return -10000 + diff
            else: return 0
        
        score = 0.0
        
        # Positional
        score += np.sum(WEIGHTS * me) - np.sum(WEIGHTS * opp)
        
        # Mobility
        my_moves = len(get_legal_moves(me, opp))
        opp_moves = len(get_legal_moves(opp, me))
        if my_moves + opp_moves > 0:
            score += 15.0 * (my_moves - opp_moves) / (my_moves + opp_moves + 1)
        
        # Corner occupancy
        my_corners = sum(1 for r, c in corners if me[r][c])
        opp_corners = sum(1 for r, c in corners if opp[r][c])
        score += 25.0 * (my_corners - opp_corners)
        
        # Stability along edges near captured corners
        # Frontier discs (discs adjacent to empty)
        my_frontier = 0
        opp_frontier = 0
        for r in range(8):
            for c in range(8):
                if me[r][c] or opp[r][c]:
                    is_frontier = False
                    for dr, dc in DIRECTIONS:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not me[nr][nc] and not opp[nr][nc]:
                            is_frontier = True
                            break
                    if is_frontier:
                        if me[r][c]:
                            my_frontier += 1
                        else:
                            opp_frontier += 1
        if my_frontier + opp_frontier > 0:
            score -= 7.0 * (my_frontier - opp_frontier) / (my_frontier + opp_frontier + 1)
        
        # Disc parity matters more in endgame
        if empty < 15:
            score += 3.0 * (my_count - opp_count)
        
        return score
    
    def move_order_key(move, me, opp):
        r, c = move
        # Corners first
        if (r, c) in corners:
            return -1000
        # Edges
        if r == 0 or r == 7 or c == 0 or c == 7:
            return -100
        # Avoid X-squares (diagonal to corner) if corner not taken
        x_squares = {(1,1):(0,0), (1,6):(0,7), (6,1):(7,0), (6,6):(7,7)}
        if (r,c) in x_squares:
            cr, cc = x_squares[(r,c)]
            if not me[cr][cc]:
                return 500
        # Avoid C-squares
        c_squares = {(0,1):(0,0), (1,0):(0,0), (0,6):(0,7), (1,7):(0,7),
                     (6,0):(7,0), (7,1):(7,0), (6,7):(7,7), (7,6):(7,7)}
        if (r,c) in c_squares:
            cr, cc = c_squares[(r,c)]
            if not me[cr][cc]:
                return 200
        return 0
    
    def alphabeta(me, opp, depth, alpha, beta, maximizing):
        if time.time() - start_time > 0.85:
            return evaluate(me, opp), True
        
        if depth == 0:
            return evaluate(me, opp), False
        
        if maximizing:
            moves = get_legal_moves(me, opp)
            if not moves:
                opp_moves = get_legal_moves(opp, me)
                if not opp_moves:
                    return evaluate(me, opp), False
                return alphabeta(me, opp, depth - 1, alpha, beta, False)
            moves.sort(key=lambda m: move_order_key(m, me, opp))
            val = -float('inf')
            for r, c in moves:
                new_me, new_opp = make_move(me, opp, r, c)
                child_val, timeout = alphabeta(new_opp, new_me, depth - 1, -beta, -alpha, False)
                child_val = -child_val if not timeout else child_val
                if timeout:
                    return evaluate(me, opp), True
                val = max(val, child_val)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, False
        else:
            moves = get_legal_moves(me, opp)
            if not moves:
                opp_moves = get_legal_moves(opp, me)
                if not opp_moves:
                    return evaluate(me, opp), False
                return alphabeta(me, opp, depth - 1, alpha, beta, True)
            moves.sort(key=lambda m: move_order_key(m, me, opp))
            val = float('inf')
            for r, c in moves:
                new_me, new_opp = make_move(me, opp, r, c)
                child_val, timeout = alphabeta(new_opp, new_me, depth - 1, -beta, -alpha, True)
                child_val = -child_val if not timeout else child_val
                if timeout:
                    return evaluate(me, opp), True
                val = min(val, child_val)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val, False
    
    # Use negamax style instead - simpler
    def negamax(me, opp, depth, alpha, beta):
        if time.time() - start_time > 0.85:
            return evaluate(me, opp), True
        
        if depth == 0:
            return evaluate(me, opp), False
        
        moves = get_legal_moves(me, opp)
        if not moves:
            opp_moves = get_legal_moves(opp, me)
            if not opp_moves:
                return evaluate(me, opp), False
            val, timeout = negamax(opp, me, depth - 1, -beta, -alpha)
            return -val, timeout
        
        moves.sort(key=lambda m: move_order_key(m, me, opp))
        val = -float('inf')
        for r, c in moves:
            new_me, new_opp = make_move(me, opp, r, c)
            child_val, timeout = negamax(new_opp, new_me, depth - 1, -beta, -alpha)
            child_val = -child_val
            if timeout:
                return evaluate(me, opp), True
            val = max(val, child_val)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return val, False
    
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    if len(legal_moves) == 1:
        r, c = legal_moves[0]
        return chr(ord('a') + c) + str(r + 1)
    
    empty_count = 64 - np.sum(you) - np.sum(opponent)
    
    # Iterative deepening
    best_move = legal_moves[0]
    max_depth = min(12, empty_count)
    
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > 0.7:
            break
        
        best_val = -float('inf')
        current_best = legal_moves[0]
        sorted_moves = sorted(legal_moves, key=lambda m: move_order_key(m, you, opponent))
        
        timed_out = False
        for r, c in sorted_moves:
            new_me, new_opp = make_move(you, opponent, r, c)
            val, timeout = negamax(new_opp, new_me, depth - 1, -float('inf'), -best_val)
            val = -val
            if timeout:
                timed_out = True
                break
            if val > best_val:
                best_val = val
                current_best = (r, c)
        
        if not timed_out:
            best_move = current_best
    
    r, c = best_move
    return chr(ord('a') + c) + str(r + 1)
