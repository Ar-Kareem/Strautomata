
import numpy as np
import time

def policy(you_list, opponent_list):
    you = np.array(you_list, dtype=np.int8)
    opp = np.array(opponent_list, dtype=np.int8)
    
    DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    ROWS, COLS = 5, 6
    
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
    
    def apply_move(me, them, r, c, nr, nc):
        me2 = me.copy()
        them2 = them.copy()
        me2[r][c] = 0
        me2[nr][nc] = 1
        them2[nr][nc] = 0
        return me2, them2
    
    def evaluate(me, them):
        my_moves = len(get_moves(me, them))
        their_moves = len(get_moves(them, me))
        return my_moves - their_moves
    
    def alphabeta(me, them, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(me, them), None
        
        if maximizing:
            moves = get_moves(me, them)
            if not moves:
                return -10000, None
            if depth == 0:
                return evaluate(me, them), moves[0]
            best_val = -100000
            best_move = moves[0]
            for m in moves:
                r, c, nr, nc, d = m
                new_me, new_them = apply_move(me, them, r, c, nr, nc)
                val, _ = alphabeta(new_them, new_me, depth - 1, -beta, -alpha, False, deadline)
                val = -val  # opponent's perspective flipped
                # Wait, let me reconsider. After my move, it's opponent's turn.
                # opponent maximizes from their perspective = minimizes from mine
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
                if time.time() > deadline:
                    break
            return best_val, best_move
        else:
            moves = get_moves(me, them)
            if not moves:
                return 10000, None
            if depth == 0:
                return -evaluate(me, them), None
            best_val = -100000
            best_move = moves[0]
            for m in moves:
                r, c, nr, nc, d = m
                new_me, new_them = apply_move(me, them, r, c, nr, nc)
                val, _ = alphabeta(new_them, new_me, depth - 1, -beta, -alpha, True, deadline)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
                if time.time() > deadline:
                    break
            return best_val, best_move
    
    # Use negamax style: always maximizing from current player's view
    def negamax(me, them, depth, alpha, beta, deadline):
        if time.time() > deadline:
            return evaluate(me, them), None
        moves = get_moves(me, them)
        if not moves:
            return -10000 - depth, None
        if depth == 0:
            return evaluate(me, them), moves[0]
        best_val = -100000
        best_move = moves[0]
        for m in moves:
            r, c, nr, nc, d = m
            new_me, new_them = apply_move(me, them, r, c, nr, nc)
            val, _ = negamax(new_them, new_me, depth - 1, -beta, -alpha, deadline)
            val = -val
            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
            if alpha >= beta:
                break
            if time.time() > deadline:
                break
        return best_val, best_move
    
    deadline = time.time() + 0.85
    moves = get_moves(you, opp)
    if not moves:
        # Should not happen per rules, but safety
        return "0,0,U"
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]},{m[4]}"
    
    best_move = moves[0]
    for depth in range(1, 30):
        if time.time() > deadline - 0.05:
            break
        val, m = negamax(you, opp, depth, -100000, 100000, deadline - 0.05)
        if m is not None:
            best_move = m
        if abs(val) > 9000:
            break
    
    return f"{best_move[0]},{best_move[1]},{best_move[4]}"
