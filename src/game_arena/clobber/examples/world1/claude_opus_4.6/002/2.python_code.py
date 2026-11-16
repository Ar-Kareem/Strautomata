
import numpy as np
import time

def policy(you_list, opponent_list):
    you = np.array(you_list, dtype=np.int8)
    opp = np.array(opponent_list, dtype=np.int8)
    ROWS, COLS = 5, 6
    DIRS = [(-1,0,'U'),(0,1,'R'),(1,0,'D'),(0,-1,'L')]
    
    def get_moves(board_me, board_opp):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if board_me[r][c] == 1:
                    for dr, dc, d in DIRS:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_opp[nr][nc] == 1:
                            moves.append((r, c, d, nr, nc))
        return moves
    
    def evaluate(me, op):
        my_moves = len(get_moves(me, op))
        opp_moves = len(get_moves(op, me))
        if my_moves == 0:
            return -10000
        if opp_moves == 0:
            return 10000
        return (my_moves - opp_moves) * 10 + np.sum(me) - np.sum(op)
    
    def apply_move(me, op, r, c, nr, nc):
        new_me = me.copy()
        new_op = op.copy()
        new_me[r][c] = 0
        new_me[nr][nc] = 1
        new_op[nr][nc] = 0
        return new_me, new_op
    
    def alphabeta(me, op, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(me, op), True
        
        if maximizing:
            moves = get_moves(me, op)
            if not moves:
                return -10000, False
            if depth == 0:
                return evaluate(me, op), False
            val = -100000
            for r, c, d, nr, nc in moves:
                new_me, new_op = apply_move(me, op, r, c, nr, nc)
                score, timeout = alphabeta(new_op, new_me, depth-1, -beta, -alpha, True, deadline)
                score = -score
                if timeout:
                    return val if val > -100000 else score, True
                val = max(val, score)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, False
        
    # Note: since we always call with maximizing=True and swap perspectives,
    # the negamax formulation is used above.
    
    moves = get_moves(you, opp)
    if not moves:
        # Should not happen if we're called, but safety
        return "0,0,U"
    if len(moves) == 1:
        r, c, d, nr, nc = moves[0]
        return f"{r},{c},{d}"
    
    deadline = time.time() + 0.85
    best_move = moves[0]
    
    for depth in range(1, 30):
        if time.time() > deadline:
            break
        best_score = -100000
        timed_out = False
        for r, c, d, nr, nc in moves:
            new_me, new_op = apply_move(you, opp, r, c, nr, nc)
            score, to = alphabeta(new_op, new_me, depth-1, -100000, -best_score, True, deadline)
            score = -score
            if to:
                timed_out = True
                break
            if score > best_score:
                best_score = score
                current_best = (r, c, d)
        if not timed_out:
            best_move = current_best
            if best_score >= 10000:
                break
    
    r, c, d = best_move
    return f"{r},{c},{d}"
