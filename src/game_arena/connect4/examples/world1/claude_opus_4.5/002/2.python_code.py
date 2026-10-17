
import numpy as np

def policy(board: list[list[int]]) -> int:
    ROWS = 6
    COLS = 7
    
    board = np.array(board)
    
    def get_valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_piece(b, col, piece):
        new_board = b.copy()
        for row in range(ROWS-1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = piece
                break
        return new_board
    
    def check_win(b, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                    return True
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                    return True
        # Diagonal (positive slope)
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                    return True
        # Diagonal (negative slope)
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                    return True
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp = -piece
        p_count = np.sum(window == piece)
        o_count = np.sum(window == opp)
        e_count = np.sum(window == 0)
        
        if p_count == 4:
            score += 100
        elif p_count == 3 and e_count == 1:
            score += 10
        elif p_count == 2 and e_count == 2:
            score += 2
        
        if o_count == 3 and e_count == 1:
            score -= 8
        
        return score
    
    def evaluate(b, piece):
        score = 0
        
        # Center column preference
        center_col = b[:, COLS//2]
        score += np.sum(center_col == piece) * 3
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                window = b[r, c:c+4]
                score += evaluate_window(window, piece)
        
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                window = b[r:r+4, c]
                score += evaluate_window(window, piece)
        
        # Diagonals
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = np.array([b[r+i][c+i] for i in range(4)])
                score += evaluate_window(window, piece)
        
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = np.array([b[r-i][c+i] for i in range(4)])
                score += evaluate_window(window, piece)
        
        return score
    
    def is_terminal(b):
        return check_win(b, 1) or check_win(b, -1) or len(get_valid_moves(b)) == 0
    
    def minimax(b, depth, alpha, beta, maximizing):
        valid_moves = get_valid_moves(b)
        terminal = is_terminal(b)
        
        if terminal:
            if check_win(b, 1):
                return (None, 1000000 + depth)
            elif check_win(b, -1):
                return (None, -1000000 - depth)
            else:
                return (None, 0)
        
        if depth == 0:
            return (None, evaluate(b, 1))
        
        # Order moves - prefer center
        valid_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        if maximizing:
            value = -float('inf')
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
    
    # Main logic
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 3  # Fallback
    
    # Check for immediate win
    for col in valid_moves:
        temp = drop_piece(board, col, 1)
        if check_win(temp, 1):
            return col
    
    # Check for immediate block
    for col in valid_moves:
        temp = drop_piece(board, col, -1)
        if check_win(temp, -1):
            return col
    
    # Avoid moves that let opponent win next turn
    safe_moves = []
    for col in valid_moves:
        temp = drop_piece(board, col, 1)
        opponent_wins = False
        for opp_col in get_valid_moves(temp):
            temp2 = drop_piece(temp, opp_col, -1)
            if check_win(temp2, -1):
                opponent_wins = True
                break
        if not opponent_wins:
            safe_moves.append(col)
    
    if safe_moves:
        valid_moves = safe_moves
    
    # Use minimax with appropriate depth
    best_col, _ = minimax(board, 6, -float('inf'), float('inf'), True)
    
    if best_col is None or best_col not in get_valid_moves(board):
        # Fallback to center-preferring valid move
        valid = get_valid_moves(board)
        valid.sort(key=lambda x: abs(x - 3))
        return valid[0]
    
    return best_col
