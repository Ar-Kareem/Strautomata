
def policy(board: list[list[int]]) -> int:
    ROWS = 6
    COLS = 7
    
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [c for c in range(COLS) if is_valid_move(board, c)]
    
    def get_next_row(board, col):
        for r in range(ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1
    
    def drop_piece(board, col, piece):
        new_board = [row[:] for row in board]
        row = get_next_row(new_board, col)
        if row != -1:
            new_board[row][col] = piece
        return new_board
    
    def check_winner(board, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp = -piece
        pc = window.count(piece)
        oc = window.count(opp)
        ec = window.count(0)
        
        if pc == 4:
            score += 10000
        elif pc == 3 and ec == 1:
            score += 50
        elif pc == 2 and ec == 2:
            score += 10
        
        if oc == 3 and ec == 1:
            score -= 80
        elif oc == 2 and ec == 2:
            score -= 5
        
        return score
    
    def evaluate_board(board, piece):
        score = 0
        
        # Center column preference
        for r in range(ROWS):
            if board[r][COLS//2] == piece:
                score += 6
            if board[r][COLS//2 - 1] == piece or board[r][COLS//2 + 1] == piece:
                score += 3
        
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
        
        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Negative diagonal
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
        
        # Order moves - center first for better pruning
        valid_moves.sort(key=lambda x: abs(x - 3))
        
        if maximizing:
            value = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_piece(board, col, 1)
                _, score = minimax(new_board, depth - 1, alpha, beta, False)
                if score > value:
                    value = score
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
                _, score = minimax(new_board, depth - 1, alpha, beta, True)
                if score < value:
                    value = score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0
    
    # Check for immediate wins
    for col in valid_moves:
        new_board = drop_piece(board, col, 1)
        if check_winner(new_board, 1):
            return col
    
    # Check for blocking opponent wins
    for col in valid_moves:
        new_board = drop_piece(board, col, -1)
        if check_winner(new_board, -1):
            return col
    
    # Use minimax with iterative deepening
    best_col = valid_moves[0] if 3 not in valid_moves else 3
    
    # Count empty cells to adjust depth
    empty_cells = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    
    if empty_cells > 30:
        depth = 6
    elif empty_cells > 20:
        depth = 8
    else:
        depth = 10
    
    best_col, _ = minimax(board, depth, float('-inf'), float('inf'), True)
    
    return best_col
