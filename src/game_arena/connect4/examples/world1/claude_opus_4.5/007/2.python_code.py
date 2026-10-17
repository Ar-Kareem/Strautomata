
def policy(board: list[list[int]]) -> int:
    import time
    
    ROWS = 6
    COLS = 7
    
    def get_valid_moves(board):
        # Order moves by center preference for better pruning
        cols = [3, 2, 4, 1, 5, 0, 6]
        return [c for c in cols if board[0][c] == 0]
    
    def drop_piece(board, col, piece):
        new_board = [row[:] for row in board]
        for row in range(ROWS - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = piece
                return new_board
        return None
    
    def check_winner(board, piece):
        for r in range(ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False
    
    def evaluate_window(window, piece):
        opp = -piece
        p_count = window.count(piece)
        o_count = window.count(opp)
        empty = window.count(0)
        
        if p_count == 4:
            return 1000
        if o_count == 4:
            return -1000
        if p_count == 3 and empty == 1:
            return 50
        if o_count == 3 and empty == 1:
            return -80  # Block opponent threats more aggressively
        if p_count == 2 and empty == 2:
            return 10
        if o_count == 2 and empty == 2:
            return -15
        return 0
    
    def evaluate(board):
        score = 0
        
        # Center column preference
        for r in range(ROWS):
            if board[r][3] == 1:
                score += 6
            elif board[r][3] == -1:
                score -= 6
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = [board[r+i][c] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Diagonals
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing):
        valid_moves = get_valid_moves(board)
        
        is_win = check_winner(board, 1)
        is_loss = check_winner(board, -1)
        
        if is_win:
            return None, 100000 + depth
        if is_loss:
            return None, -100000 - depth
        if not valid_moves:
            return None, 0
        if depth == 0:
            return None, evaluate(board)
        
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
            return best_col, value
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
            return best_col, value
    
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 3
    
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
    
    # Iterative deepening with time limit
    best_move = valid_moves[0]
    start = time.time()
    
    for depth in range(1, 20):
        if time.time() - start > 0.7:
            break
        move, score = minimax(board, depth, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
        # Early exit if we found a winning move
        if score > 50000:
            break
    
    return best_move
