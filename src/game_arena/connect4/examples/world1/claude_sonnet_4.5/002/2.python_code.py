
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning.
    """
    ROWS = 6
    COLS = 7
    
    def get_valid_moves(b):
        """Return list of valid column indices."""
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_piece(b, col, piece):
        """Return new board with piece dropped in column. Returns None if invalid."""
        for row in range(ROWS - 1, -1, -1):
            if b[row][col] == 0:
                new_board = [row[:] for row in b]
                new_board[row][col] = piece
                return new_board
        return None
    
    def check_winner(b, piece):
        """Check if piece has won."""
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(b[r][c + i] == piece for i in range(4)):
                    return True
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(b[r + i][c] == piece for i in range(4)):
                    return True
        
        # Diagonal (positive slope)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(b[r - i][c + i] == piece for i in range(4)):
                    return True
        
        # Diagonal (negative slope)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(b[r + i][c + i] == piece for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, piece):
        """Evaluate a window of 4 cells."""
        score = 0
        opp = -piece
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        
        if window.count(opp) == 3 and window.count(0) == 1:
            score -= 4
        
        return score
    
    def evaluate_position(b, piece):
        """Heuristic evaluation of board position."""
        score = 0
        
        # Center column preference
        center_array = [b[r][COLS // 2] for r in range(ROWS)]
        score += center_array.count(piece) * 3
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [b[r][c + i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [b[r + i][c] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Diagonal (positive slope)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [b[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Diagonal (negative slope)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing, piece):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(b)
        
        if depth == 0 or len(valid_moves) == 0:
            return None, evaluate_position(b, piece)
        
        if check_winner(b, piece):
            return None, 1000000
        if check_winner(b, -piece):
            return None, -1000000
        
        if maximizing:
            value = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_piece(b, col, piece)
                if new_board:
                    _, new_score = minimax(new_board, depth - 1, alpha, beta, False, piece)
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
                new_board = drop_piece(b, col, -piece)
                if new_board:
                    _, new_score = minimax(new_board, depth - 1, alpha, beta, True, piece)
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
        return 0
    
    # Check for immediate win
    for col in valid_moves:
        temp_board = drop_piece(board, col, 1)
        if temp_board and check_winner(temp_board, 1):
            return col
    
    # Check for immediate block
    for col in valid_moves:
        temp_board = drop_piece(board, col, -1)
        if temp_board and check_winner(temp_board, -1):
            return col
    
    # Use minimax
    best_col, _ = minimax(board, 5, float('-inf'), float('inf'), True, 1)
    
    return best_col if best_col is not None else valid_moves[0]
