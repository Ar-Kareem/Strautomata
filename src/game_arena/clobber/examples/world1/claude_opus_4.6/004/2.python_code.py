
import numpy as np
import time

def policy(you_list, opponent_list):
    you = np.array(you_list, dtype=np.int8)
    opp = np.array(opponent_list, dtype=np.int8)
    
    ROWS, COLS = 5, 6
    DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    def get_moves(board_me, board_opp):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if board_me[r][c] == 1:
                    for dr, dc, d in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_opp[nr][nc] == 1:
                            moves.append((r, c, d, nr, nc))
        return moves
    
    def evaluate(board_me, board_opp):
        my_moves = len(get_moves(board_me, board_opp))
        opp_moves = len(get_moves(board_opp, board_me))
        return my_moves - opp_moves
    
    def apply_move(board_me, board_opp, r, c, nr, nc):
        bm = board_me.copy()
        bo = board_opp.copy()
        bm[r][c] = 0
        bm[nr][nc] = 1
        bo[nr][nc] = 0
        return bm, bo
    
    def alphabeta(board_me, board_opp, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            raise TimeoutError
        
        moves = get_moves(board_me, board_opp) if maximizing else get_moves(board_me, board_opp)
        
        if maximizing:
            my_moves = get_moves(board_me, board_opp)
            if not my_moves:
                return -1000, None
            if depth == 0:
                return evaluate(board_me, board_opp), None
            best_val = -10000
            best_move = my_moves[0]
            # Sort moves by heuristic
            scored = []
            for m in my_moves:
                nm, no = apply_move(board_me, board_opp, m[0], m[1], m[3], m[4])
                scored.append((-len(get_moves(no, nm)), m, nm, no))
            scored.sort(key=lambda x: x[0])
            for s, m, nm, no in scored:
                val, _ = alphabeta(no, nm, depth - 1, -beta, -alpha, False, deadline)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return best_val, best_move
        else:
            opp_moves = get_moves(board_me, board_opp)
            if not opp_moves:
                return -1000, None
            if depth == 0:
                return evaluate(board_me, board_opp), None
            best_val = -10000
            best_move = opp_moves[0]
            for m in opp_moves:
                nm, no = apply_move(board_me, board_opp, m[0], m[1], m[3], m[4])
                val, _ = alphabeta(no, nm, depth - 1, -beta, -alpha, True, deadline)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return best_val, best_move
    
    deadline = time.time() + 0.85
    legal = get_moves(you, opp)
    if not legal:
        return "0,0,U"  # shouldn't happen
    
    best_move = legal[0]
    for depth in range(1, 30):
        try:
            val, move = alphabeta(you, opp, depth, -10000, 10000, True, deadline)
            if move:
                best_move = move
            if abs(val) >= 900:
                break
        except TimeoutError:
            break
        if time.time() > deadline:
            break
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
