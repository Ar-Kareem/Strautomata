
import numpy as np

def policy(board: list[list[int]]) -> int:
    board = np.array(board)
    ROWS, COLS = 6, 7
    
    def get_valid_cols(b):
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_piece(b, col, player):
        b = b.copy()
        for r in range(ROWS-1, -1, -1):
            if b[r][col] == 0:
                b[r][col] = player
                break
        return b
    
    def check_win(b, player):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        return False
    
    def evaluate_window(window, player):
        opp = -player
        score = 0
        player_count = np.sum(window == player)
        empty_count = np.sum(window == 0)
        opp_count = np.sum(window == opp)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opp_count == 3 and empty_count == 1:
            score -= 4
        
        return score
    
    def evaluate(b):
        score = 0
        # Center column preference
        center = b[:, COLS//2]
        score += np.sum(center == 1) * 3
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                window = b[r, c:c+4]
                score += evaluate_window(window, 1)
        
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                window = b[r:r+4, c]
                score += evaluate_window(window, 1)
        
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = np.array([b[r+i][c+i] for i in range(4)])
                score += evaluate_window(window, 1)
        
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = np.array([b[r-i][c+i] for i in range(4)])
                score += evaluate_window(window, 1)
        
        return score
    
    def order_moves(cols):
        # Prioritize center columns
        return sorted(cols, key=lambda c: abs(c - COLS//2))
    
    def minimax(b, depth, alpha, beta, maximizing):
        valid_cols = get_valid_cols(b)
        
        if check_win(b, 1):
            return (None, 100000 + depth)
        if check_win(b, -1):
            return (None, -100000 - depth)
        if len(valid_cols) == 0:
            return (None, 0)
        if depth == 0:
            return (None, evaluate(b))
        
        valid_cols = order_moves(valid_cols)
        
        if maximizing:
            value = -float('inf')
            best_col = valid_cols[0]
            for col in valid_cols:
                new_board = drop_piece(b, col, 1)
                _, new_score = minimax(new_board, depth-1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = valid_cols[0]
            for col in valid_cols:
                new_board = drop_piece(b, col, -1)
                _, new_score = minimax(new_board, depth-1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    valid_cols = get_valid_cols(board)
    
    if not valid_cols:
        return 0  # Shouldn't happen
    
    # Check for immediate win
    for col in valid_cols:
        temp = drop_piece(board, col, 1)
        if check_win(temp, 1):
            return col
    
    # Check for immediate block
    for col in valid_cols:
        temp = drop_piece(board, col, -1)
        if check_win(temp, -1):
            return col
    
    # Use minimax with depth 6
    best_col, _ = minimax(board, 6, -float('inf'), float('inf'), True)
    return best_col
