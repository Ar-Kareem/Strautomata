
def policy(board: list[list[int]]) -> int:
    import time
    
    start_time = time.time()
    TIME_LIMIT = 0.9
    ROWS, COLS = 6, 7
    WIN_SCORE = 100000
    
    def valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop(b, col, p):
        b = [row[:] for row in b]
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                b[r][col] = p
                return b
        return None
    
    def wins(b, p):
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3] == p:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c] == p:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3] == p:
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3] == p:
                    return True
        return False
    
    def eval_window(w):
        m, o, e = w.count(1), w.count(-1), w.count(0)
        if m and o:
            return 0
        if m == 3 and e == 1:
            return 50
        if o == 3 and e == 1:
            return -50
        if m == 2 and e == 2:
            return 10
        if o == 2 and e == 2:
            return -10
        return 0
    
    def evaluate(b):
        score = 0
        for r in range(ROWS):
            for c in range(COLS):
                w = 4 - abs(c - 3)
                if b[r][c] == 1:
                    score += w
                elif b[r][c] == -1:
                    score -= w
        
        for r in range(ROWS):
            for c in range(COLS - 3):
                score += eval_window([b[r][c+i] for i in range(4)])
        for r in range(ROWS - 3):
            for c in range(COLS):
                score += eval_window([b[r+i][c] for i in range(4)])
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += eval_window([b[r+i][c+i] for i in range(4)])
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += eval_window([b[r-i][c+i] for i in range(4)])
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start_time > TIME_LIMIT:
            return None, evaluate(b)
        
        moves = valid_moves(b)
        
        if wins(b, 1):
            return None, WIN_SCORE + depth
        if wins(b, -1):
            return None, -WIN_SCORE - depth
        if not moves:
            return None, 0
        if depth == 0:
            return None, evaluate(b)
        
        moves = sorted(moves, key=lambda c: abs(c - 3))
        
        if maximizing:
            best = (moves[0], float('-inf'))
            for col in moves:
                _, val = minimax(drop(b, col, 1), depth - 1, alpha, beta, False)
                if val > best[1]:
                    best = (col, val)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return best
        else:
            best = (moves[0], float('inf'))
            for col in moves:
                _, val = minimax(drop(b, col, -1), depth - 1, alpha, beta, True)
                if val < best[1]:
                    best = (col, val)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return best
    
    moves = valid_moves(board)
    if not moves:
        return 0
    
    for c in moves:
        if wins(drop(board, c, 1), 1):
            return c
    
    blocks = [c for c in moves if wins(drop(board, c, -1), -1)]
    if blocks:
        return blocks[0]
    
    safe = []
    for c in moves:
        nb = drop(board, c, 1)
        if not any(wins(drop(nb, oc, -1), -1) for oc in valid_moves(nb)):
            safe.append(c)
    
    search_moves = safe if safe else moves
    best_col = 3 if 3 in search_moves else search_moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > TIME_LIMIT * 0.75:
            break
        col, score = minimax(board, depth, float('-inf'), float('inf'), True)
        if col is not None and col in search_moves:
            best_col = col
        if abs(score) > WIN_SCORE - 50:
            break
    
    return best_col
