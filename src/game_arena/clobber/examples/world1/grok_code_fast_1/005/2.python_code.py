
import numpy as np
import math

def policy(you, opponent):
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Collect legal moves for the current player (you)
    moves = []
    for r in range(5):
        for c in range(6):
            if you[r, c]:
                directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
                for dr, dc, dir in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr, nc]:
                        moves.append((r, c, dir))
    
    if not moves:
        # Should not happen in valid games, but return a format-compliant string
        return '0,0,U'
    
    INF = 10000
    DEPTH = 2
    
    def evaluate(bd_you, bd_opp):
        """Evaluate board as my mobility - opponent's mobility."""
        my_mob = 0
        opp_mob = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for r in range(5):
            for c in range(6):
                if bd_you[r, c]:
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and bd_opp[nr, nc]:
                            my_mob += 1
                if bd_opp[r, c]:
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and bd_you[nr, nc]:
                            opp_mob += 1
        return my_mob - opp_mob
    
    def apply_move(bd_mine, bd_opp, r, c, dir):
        """Apply a move: mover captures opponent piece."""
        bd_mine_new = bd_mine.copy()
        bd_opp_new = bd_opp.copy()
        if dir == 'U':
            nr, nc = r - 1, c
        elif dir == 'D':
            nr, nc = r + 1, c
        elif dir == 'L':
            nr, nc = r, c - 1
        elif dir == 'R':
            nr, nc = r, c + 1
        bd_mine_new[r, c] = 0
        bd_mine_new[nr, nc] = 1
        bd_opp_new[nr, nc] = 0
        return bd_mine_new, bd_opp_new
    
    def minimax(bd_y, bd_o, depth, is_max, alpha=-INF, beta=INF):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate(bd_y, bd_o)
        
        directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
        legal_ms = []
        if is_max:  # My turn
            for r in range(5):
                for c in range(6):
                    if bd_y[r, c]:
                        for dr, dc, dir in directions:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 5 and 0 <= nc < 6 and bd_o[nr, nc]:
                                legal_ms.append((r, c, dir))
            if not legal_ms:
                return -INF  # I lose
            max_eval = -INF
            for m in legal_ms:
                ny, no = apply_move(bd_y, bd_o, *m)
                ev = minimax(ny, no, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:  # Opponent's turn
            for r in range(5):
                for c in range(6):
                    if bd_o[r, c]:
                        for dr, dc, dir in directions:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 5 and 0 <= nc < 6 and bd_y[nr, nc]:
                                legal_ms.append((r, c, dir))
            if not legal_ms:
                return INF  # Opponent loses, good for me
            min_eval = INF
            for m in legal_ms:
                no, ny = apply_move(bd_o, bd_y, *m)
                ev = minimax(ny, no, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # Select best move using minimax
    best_eval = -INF
    best_move = None
    for move in moves:
        ny, no = apply_move(you, opponent, *move)
        ev = minimax(ny, no, DEPTH, False)
        if ev > best_eval:
            best_eval = ev
            best_move = move
    
    # Format and return the move
    r, c, dir = best_move
    return f"{r},{c},{dir}"
