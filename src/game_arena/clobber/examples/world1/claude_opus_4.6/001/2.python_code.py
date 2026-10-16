
import numpy as np
import time

def policy(you_list, opponent_list):
    you = np.array(you_list, dtype=np.int8)
    opp = np.array(opponent_list, dtype=np.int8)
    
    DIRS = [(-1,0,'U'),(0,1,'R'),(1,0,'D'),(0,-1,'L')]
    ROWS, COLS = 5, 6
    
    def get_moves(board_me, board_them):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if board_me[r][c] == 1:
                    for dr, dc, d in DIRS:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_them[nr][nc] == 1:
                            moves.append((r, c, nr, nc, d))
        return moves
    
    def evaluate(me, them, is_my_turn):
        my_moves = len(get_moves(me, them))
        their_moves = len(get_moves(them, me))
        if is_my_turn and my_moves == 0:
            return -10000
        if not is_my_turn and their_moves == 0:
            return 10000
        return (my_moves - their_moves) * 10
    
    def apply_move(me, them, move):
        r, c, nr, nc, d = move
        new_me = me.copy()
        new_them = them.copy()
        new_me[r][c] = 0
        new_me[nr][nc] = 1
        new_them[nr][nc] = 0
        return new_me, new_them
    
    def alphabeta(me, them, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(me, them, maximizing), True
        
        if maximizing:
            moves = get_moves(me, them)
            if not moves:
                return -10000, False
            if depth == 0:
                return evaluate(me, them, True), False
            val = -100000
            for move in moves:
                new_me, new_them = apply_move(me, them, move)
                child_val, timeout = alphabeta(new_them, new_me, depth-1, -beta, -alpha, False, deadline)
                child_val = -child_val
                if timeout:
                    return val if val > -100000 else child_val, True
                val = max(val, child_val)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, False
        else:
            moves = get_moves(me, them)
            if not moves:
                return 10000, False
            if depth == 0:
                return -evaluate(me, them, True), False
            val = -100000
            for move in moves:
                new_me, new_them = apply_move(me, them, move)
                child_val, timeout = alphabeta(new_them, new_me, depth-1, -beta, -alpha, True, deadline)
                child_val = -child_val
                if timeout:
                    return val if val > -100000 else child_val, True
                val = max(val, child_val)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, False
    
    moves = get_moves(you, opp)
    if not moves:
        return "0,0,U"  # shouldn't happen
    
    best_move = moves[0]
    deadline = time.time() + 0.8
    
    for depth in range(1, 30):
        if time.time() > deadline:
            break
        best_val = -200000
        best_candidate = moves[0]
        for move in moves:
            new_me, new_opp = apply_move(you, opp, move)
            val, timeout = alphabeta(new_opp, new_me, depth-1, -200000, 200000, True, deadline)
            val = -val
            if timeout:
                break
            if val > best_val:
                best_val = val
                best_candidate = move
        else:
            best_move = best_candidate
            if best_val >= 10000 or best_val <= -10000:
                break
            continue
        break
    
    r, c, nr, nc, d = best_move
    return f"{r},{c},{d}"
