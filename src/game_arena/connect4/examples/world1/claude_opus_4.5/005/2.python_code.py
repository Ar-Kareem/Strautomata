
import numpy as np

def policy(board: list[list[int]]) -> int:
    ROWS = 6
    COLS = 7
    
    board = np.array(board, dtype=np.int8)
    
    def get_valid_moves(b):
        return [c for c in range(COLS) if b[0, c] == 0]
    
    def drop_piece(b, col, piece):
        new_board = b.copy()
        for row in range(ROWS-1, -1, -1):
            if new_board[row, col] == 0:
                new_board[row, col] = piece
                return new_board
        return None
    
    def check_win(b, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if b[r, c] == piece and b[r, c+1] == piece and b[r, c+2] == piece and b[r, c+3] == piece:
                    return True
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                if b[r, c] == piece and b[r+1, c] == piece and b[r+2, c] == piece and b[r+3, c] == piece:
                    return True
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if b[r, c] == piece and b[r-1, c+1] == piece and b[r-2, c+2] == piece and b[r-3, c+3] == piece:
                    return True
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if b[r, c] == piece and b[r+1, c+1] == piece and b[r+2, c+2] == piece and b[r+3, c+3] == piece:
                    return True
        return False
    
    def count_window(window, piece):
        return np.sum(window == piece)
    
    def evaluate_window(window, piece):
        score = 0
        opp = -piece
        p_count = count_window(window, piece)
        o_count = count_window(window, opp)
        empty = count_window(window, 0)
        
        if p_count == 4:
            score += 100000
        elif p_count == 3 and empty == 1:
            score += 50
        elif p_count == 2 and empty == 2:
            score += 10
        
        if o_count == 3 and empty == 1:
            score -= 80
        elif o_count == 2 and empty == 2:
            score -= 8
        
        return score
    
    def score_position(b, piece):
        score = 0
        
        # Center column preference
        center = b[:, COLS//2]
        score += np.sum(center == piece) * 6
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                window = b[r, c:c+4]
                score += evaluate_window(window, piece)
        
        # Vertical
        for c in range(COLS):
            for r in range(ROWS-3):
                window = b[r:r+4, c]
                score += evaluate_window(window, piece)
        
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = np.array([b[r-i, c+i] for i in range(4)])
                score += evaluate_window(window, piece)
        
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = np.array([b[r+i, c+i] for i in range(4)])
                score += evaluate_window(window, piece)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        valid = get_valid_moves(b)
        
        if check_win(b, 1):
            return None, 1000000 + depth
        if check_win(b, -1):
            return None, -1000000 - depth
        if len(valid) == 0:
            return None, 0
        if depth == 0:
            return None, score_position(b, 1)
        
        # Order moves - center first
        valid = sorted(valid, key=lambda x: abs(x - 3))
        
        if maximizing:
            value = -float('inf')
            best_col = valid[0]
            for col in valid:
                new_b = drop_piece(b, col, 1)
                _, new_score = minimax(new_b, depth-1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = valid[0]
            for col in valid:
                new_b = drop_piece(b, col, -1)
                _, new_score = minimax(new_b, depth-1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 0
    
    # Check for immediate win
    for col in valid_moves:
        new_b = drop_piece(board, col, 1)
        if check_win(new_b, 1):
            return col
    
    # Block immediate opponent win
    for col in valid_moves:
        new_b = drop_piece(board, col, -1)
        if check_win(new_b, -1):
            return col
    
    # Use minimax with appropriate depth
    best_col, _ = minimax(board, 7, -float('inf'), float('inf'), True)
    return best_col
