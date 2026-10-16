
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    b = np.array(board, dtype=np.int8)
    
    # All 49 winning lines
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])
            lines.append([(i, k, j) for k in range(3)])
            lines.append([(k, i, j) for k in range(3)])
    for i in range(3):
        lines.append([(i, k, k) for k in range(3)])
        lines.append([(i, k, 2-k) for k in range(3)])
        lines.append([(k, i, k) for k in range(3)])
        lines.append([(k, i, 2-k) for k in range(3)])
        lines.append([(k, k, i) for k in range(3)])
        lines.append([(k, 2-k, i) for k in range(3)])
    lines.append([(k, k, k) for k in range(3)])
    lines.append([(k, k, 2-k) for k in range(3)])
    lines.append([(k, 2-k, k) for k in range(3)])
    lines.append([(2-k, k, k) for k in range(3)])
    
    lines_arr = [tuple(l) for l in lines]
    
    def check_win(b, player):
        for l in lines_arr:
            if all(b[p] == player for p in l):
                return True
        return False
    
    def get_empty(b):
        return list(zip(*np.where(b == 0)))
    
    def evaluate(b):
        score = 0
        for l in lines_arr:
            vals = [b[p] for p in l]
            s1 = vals.count(1)
            sm1 = vals.count(-1)
            if sm1 == 0:
                if s1 == 3: score += 10000
                elif s1 == 2: score += 50
                elif s1 == 1: score += 5
            if s1 == 0:
                if sm1 == 3: score -= 10000
                elif sm1 == 2: score -= 50
                elif sm1 == 1: score -= 5
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        if check_win(b, 1): return 100000 + depth
        if check_win(b, -1): return -100000 - depth
        empty = get_empty(b)
        if not empty or depth == 0:
            return evaluate(b)
        
        if maximizing:
            val = -999999
            for move in empty:
                b[move] = 1
                val = max(val, minimax(b, depth-1, alpha, beta, False))
                b[move] = 0
                alpha = max(alpha, val)
                if alpha >= beta: break
            return val
        else:
            val = 999999
            for move in empty:
                b[move] = -1
                val = min(val, minimax(b, depth-1, alpha, beta, True))
                b[move] = 0
                beta = min(beta, val)
                if alpha >= beta: break
            return val
    
    empty = get_empty(b)
    
    # Immediate win or block
    for m in empty:
        b[m] = 1
        if check_win(b, 1): b[m] = 0; return m
        b[m] = 0
    for m in empty:
        b[m] = -1
        if check_win(b, -1): b[m] = 0; return m
        b[m] = 0
    
    n_empty = len(empty)
    depth = 3 if n_empty > 16 else (4 if n_empty > 10 else (5 if n_empty > 6 else 7))
    
    best_move = empty[0]
    best_val = -999999
    # Sort moves: center first, then by heuristic value
    def move_priority(m):
        return -sum(abs(c - 1) for c in m)
    empty.sort(key=move_priority)
    
    for m in empty:
        b[m] = 1
        val = minimax(b, depth-1, best_val, 999999, False)
        b[m] = 0
        if val > best_val:
            best_val = val
            best_move = m
    
    return best_move
