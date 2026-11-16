
def policy(board: list[list[int]]) -> int:
    import copy
    
    ROWS = 6
    COLS = 7
    
    def get_valid_moves(board):
        return [c for c in range(COLS) if board[0][c] == 0]
    
    def drop_piece(board, col, piece):
        new_board = copy.deepcopy(board)
        for row in range(ROWS - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = piece
                return new_board
        return None
    
    def check_winner(board, piece):
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(board[r][c+i] == piece for i in range(4)):
                    return True
        # Check vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(board[r+i][c] == piece for i in range(4)):
                    return True
        # Check diagonal (positive slope)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(board[r+i][c+i] == piece for i in range(4)):
                    return True
        # Check diagonal (negative slope)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(board[r-i][c+i] == piece for i in range(4)):
                    return True
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4
        
        return score
    
    def evaluate_board(board, piece):
        score = 0
        
        # Center column preference
        center_col = [board[r][COLS//2] for r in range(ROWS)]
        center_count = center_col.count(piece)
        score += center_count * 3
        
        # Adjacent to center
        for adj in [2, 4]:
            adj_col = [board[r][adj] for r in range(ROWS)]
            score += adj_col.count(piece) * 2
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = [board[r+i][c] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Diagonal positive
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Diagonal negative
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        return score
    
    def is_terminal(board):
        return check_winner(board, 1) or check_winner(board, -1) or len(get_valid_moves(board)) == 0
    
    def minimax(board, depth, alpha, beta, maximizing):
        valid_moves = get_valid_moves(board)
        terminal = is_terminal(board)
        
        if terminal:
            if check_winner(board, 1):
                return (None, 1000000 + depth)
            elif check_winner(board, -1):
                return (None, -1000000 - depth)
            else:
                return (None, 0)
        
        if depth == 0:
            return (None, evaluate_board(board, 1))
        
        # Order moves - center columns first
        valid_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        if maximizing:
            value = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_piece(board, col, 1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return (best_col, value)
        else:
            value = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_piece(board, col, -1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return (best_col, value)
    
    valid_moves = get_valid_moves(board)
    
    # Check for immediate win
    for col in valid_moves:
        new_board = drop_piece(board, col, 1)
        if check_winner(new_board, 1):
            return col
    
    # Check for immediate block
    for col in valid_moves:
        new_board = drop_piece(board, col, -1)
        if check_winner(new_board, -1):
            return col
    
    # Count pieces to determine game stage
    pieces = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] != 0)
    
    # Adjust depth based on game state
    if pieces < 8:
        depth = 6
    elif pieces < 20:
        depth = 7
    else:
        depth = 8
    
    # Use minimax
    best_col, _ = minimax(board, depth, float('-inf'), float('inf'), True)
    return best_col
