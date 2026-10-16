
import numpy as np
import time

def policy(you_list, opponent_list):
    you = np.array(you_list, dtype=np.int8)
    opp = np.array(opponent_list, dtype=np.int8)
    
    ROWS, COLS = 5, 6
    DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    
    def get_moves(board_me, board_them):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if board_me[r][c] == 1:
                    for dr, dc, d in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_them[nr][nc] == 1:
                            moves.append((r, c, nr, nc, d))
        return moves
    
    def evaluate(board_me, board_them):
        my_moves = len(get_moves(board_me, board_them))
        their_moves = len(get_moves(board_them, board_me))
        # Mobility difference is primary
        score = (my_moves - their_moves) * 10
        # Secondary: pieces near opponents are more valuable
        for r in range(ROWS):
            for c in range(COLS):
                if board_me[r][c]:
                    for dr, dc, _ in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_them[nr][nc]:
                            score += 1
                if board_them[r][c]:
                    for dr, dc, _ in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board_me[nr][nc]:
                            score -= 1
        return score
    
    def alphabeta(me, them, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(me, them), None
        moves = get_moves(me, them) if maximizing else get_moves(them, me)
        if not moves:
            return (-10000 if maximizing else 10000), None
        if depth == 0:
            return evaluate(me, them), None
        
        best_move = moves[0]
        if maximizing:
            val = -100000
            for m in moves:
                r, c, nr, nc, d = m
                new_me = me.copy(); new_them = them.copy()
                new_me[r][c] = 0; new_me[nr][nc] = 1; new_them[nr][nc] = 0
                v, _ = alphabeta(new_me, new_them, depth-1, alpha, beta, False, deadline)
                if v > val:
                    val = v; best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, best_move
        else:
            val = 100000
            for m in moves:
                r, c, nr, nc, d = m
                new_them = them.copy(); new_me = me.copy()
                new_them[r][c] = 0; new_them[nr][nc] = 1; new_me[nr][nc] = 0
                v, _ = alphabeta(new_me, new_them, depth-1, alpha, beta, True, deadline)
                if v < val:
                    val = v; best_move = m
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val, best_move
    
    deadline = time.time() + 0.85
    legal = get_moves(you, opp)
    if len(legal) == 1:
        m = legal[0]
        return f"{m[0]},{m[1]},{m[4]}"
    
    best_move = legal[0]
    for depth in range(1, 30):
        if time.time() > deadline:
            break
        val, move = alphabeta(you.copy(), opp.copy(), depth, -100000, 100000, True, deadline)
        if move:
            best_move = move
        if abs(val) >= 9000:
            break
    
    return f"{best_move[0]},{best_move[1]},{best_move[4]}"
