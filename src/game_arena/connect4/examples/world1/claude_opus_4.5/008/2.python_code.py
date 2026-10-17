
import numpy as np

def policy(board: list[list[int]]) -> int:
    board = np.array(board)
    ROWS, COLS = 6, 7
    
    def get_valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_piece(b, col, player):
        new_board = b.copy()
        for row in range(ROWS-1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return None
    
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
        # Diagonal (positive slope)
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # Diagonal (negative slope)
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False
    
    def evaluate_window(window, player):
        opponent = -player
        score = 0
        player_count = np.sum(window == player)
        opponent_count = np.sum(window == opponent)
        empty_count = np.sum(window == 0)
        
        if player_count == 4:
            score += 100000
        elif player_count == 3 and empty_count == 1:
            score += 50
        elif player_count == 2 and empty_count == 2:
            score += 5
        
        if opponent_count == 3 and empty_count == 1:
            score -= 80
        elif opponent_count == 2 and empty_count == 2:
            score -= 3
        
        return score
    
    def evaluate_board(b, player):
        score = 0
        # Center column preference
        center_col = COLS // 2
        center_count = np.sum(b[:, center_col] == player)
        score += center_count * 6
        
        # Horizontal windows
        for r in range(ROWS):
            for c in range(COLS-3):
                window = b[r, c:c+4]
                score += evaluate_window(window, player)
        
        # Vertical windows
        for r in range(ROWS-3):
            for c in range(COLS):
                window = b[r:r+4, c]
                score += evaluate_window(window, player)
        
        # Positive diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = np.array([b[r+i, c+i] for i in range(4)])
                score += evaluate_window(window, player)
        
        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = np.array([b[r-i, c+i] for i in range(4)])
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        valid_moves = get_valid_moves(b)
        
        is_win_1 = check_win(b, 1)
        is_win_m1 = check_win(b, -1)
        
        if is_win_1:
            return None, 10000000 + depth
        if is_win_m1:
            return None, -10000000 - depth
        if len(valid_moves) == 0:
            return None, 0
        if depth == 0:
            return None, evaluate_board(b, 1)
        
        # Order moves (center first for better pruning)
        valid_moves.sort(key=lambda x: abs(x - 3))
        
        if maximizing:
            value = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
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
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_piece(b, col, -1)
                _, new_score = minimax(new_board, depth-1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 3  # Fallback
    
    # Check for immediate winning move
    for col in valid_moves:
        temp = drop_piece(board, col, 1)
        if check_win(temp, 1):
            return col
    
    # Check for immediate block needed
    for col in valid_moves:
        temp = drop_piece(board, col, -1)
        if check_win(temp, -1):
            return col
    
    # Use minimax with iterative deepening approach - start with depth 6
    best_col, _ = minimax(board, 6, float('-inf'), float('inf'), True)
    
    if best_col is None or best_col not in valid_moves:
        # Fallback to center-biased choice
        valid_moves.sort(key=lambda x: abs(x - 3))
        return valid_moves[0]
    
    return best_col
