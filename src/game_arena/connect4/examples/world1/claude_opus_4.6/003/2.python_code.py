
import time
import random

def policy(board: list[list[int]]) -> int:
    ROWS, COLS = 6, 7
    b = [row[:] for row in board]
    
    def get_valid_cols():
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_row(col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return -1
    
    def check_win(player):
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3] == player:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c] == player:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3] == player:
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3] == player:
                    return True
        return False
    
    def evaluate():
        score = 0
        # Center preference
        for r in range(ROWS):
            if b[r][3] == 1:
                score += 3
            elif b[r][3] == -1:
                score -= 3
        
        # Evaluate all windows of 4
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
    
    def eval_window(w):
        p1 = w.count(1)
        p2 = w.count(-1)
        empty = w.count(0)
        if p1 == 4: return 10000
        if p2 == 4: return -10000
        if p1 == 3 and empty == 1: return 50
        if p2 == 3 and empty == 1: return -50
        if p1 == 2 and empty == 2: return 5
        if p2 == 2 and empty == 2: return -5
        return 0
    
    move_order = [3, 2, 4, 1, 5, 0, 6]
    
    def minimax(depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            raise TimeoutError
        
        if check_win(1): return 100000 + depth, -1
        if check_win(-1): return -100000 - depth, -1
        
        valid = [c for c in move_order if b[0][c] == 0]
        if not valid: return 0, -1
        if depth == 0: return evaluate(), -1
        
        if maximizing:
            best_score = -float('inf')
            best_col = valid[0]
            for c in valid:
                r = drop_row(c)
                b[r][c] = 1
                sc, _ = minimax(depth - 1, alpha, beta, False, deadline)
                b[r][c] = 0
                if sc > best_score:
                    best_score = sc
                    best_col = c
                alpha = max(alpha, sc)
                if alpha >= beta:
                    break
            return best_score, best_col
        else:
            best_score = float('inf')
            best_col = valid[0]
            for c in valid:
                r = drop_row(c)
                b[r][c] = -1
                sc, _ = minimax(depth - 1, alpha, beta, True, deadline)
                b[r][c] = 0
                if sc < best_score:
                    best_score = sc
                    best_col = c
                beta = min(beta, sc)
                if alpha >= beta:
                    break
            return best_score, best_col
    
    valid_cols = get_valid_cols()
    if not valid_cols:
        return 0
    
    # Check immediate wins
    for c in valid_cols:
        r = drop_row(c)
        b[r][c] = 1
        if check_win(1):
            b[r][c] = 0
            return c
        b[r][c] = 0
    
    # Block immediate opponent wins
    for c in valid_cols:
        r = drop_row(c)
        b[r][c] = -1
        if check_win(-1):
            b[r][c] = 0
            return c
        b[r][c] = 0
    
    deadline = time.time() + 0.85
    best_move = valid_cols[0]
    # prefer center
    for c in move_order:
        if c in valid_cols:
            best_move = c
            break
    
    try:
        for depth in range(1, 43):
            if time.time() > deadline:
                break
            sc, mv = minimax(depth, -float('inf'), float('inf'), True, deadline)
            if mv >= 0 and mv in valid_cols:
                best_move = mv
            # If we found a winning move, stop searching
            if sc >= 90000:
                break
    except TimeoutError:
        pass
    
    return best_move
