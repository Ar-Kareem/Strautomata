
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_winner(board):
        """Check if there's a winner on the board"""
        # Check all possible lines in 3D
        # Rows (within each layer)
        for z in range(3):
            for y in range(3):
                if board[z][y][0] == board[z][y][1] == board[z][y][2] != 0:
                    return board[z][y][0]
        
        # Columns (within each layer)
        for z in range(3):
            for x in range(3):
                if board[z][0][x] == board[z][1][x] == board[z][2][x] != 0:
                    return board[z][0][x]
        
        # Layer diagonals
        for z in range(3):
            if board[z][0][0] == board[z][1][1] == board[z][2][2] != 0:
                return board[z][0][0]
            if board[z][0][2] == board[z][1][1] == board[z][2][0] != 0:
                return board[z][0][2]
        
        # Vertical lines (through layers)
        for y in range(3):
            for x in range(3):
                if board[0][y][x] == board[1][y][x] == board[2][y][x] != 0:
                    return board[0][y][x]
        
        # Vertical diagonals (through layers and rows)
        for x in range(3):
            if board[0][0][x] == board[1][1][x] == board[2][2][x] != 0:
                return board[0][0][x]
            if board[0][2][x] == board[1][1][x] == board[2][0][x] != 0:
                return board[0][2][x]
        
        # Vertical diagonals (through layers and columns)
        for y in range(3):
            if board[0][y][0] == board[1][y][1] == board[2][y][2] != 0:
                return board[0][y][0]
            if board[0][y][2] == board[1][y][1] == board[2][y][0] != 0:
                return board[0][y][2]
        
        # 3D diagonals (corner to corner)
        if board[0][0][0] == board[1][1][1] == board[2][2][2] != 0:
            return board[0][0][0]
        if board[0][0][2] == board[1][1][1] == board[2][2][0] != 0:
            return board[0][0][2]
        if board[0][2][0] == board[1][1][1] == board[2][0][2] != 0:
            return board[0][2][0]
        if board[0][2][2] == board[1][1][1] == board[2][0][0] != 0:
            return board[0][2][2]
        
        return 0
    
    def get_empty_cells(board):
        """Get all empty cell positions"""
        empty = []
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == 0:
                        empty.append((z, y, x))
        return empty
    
    def is_terminal(board):
        """Check if the game is over"""
        return get_winner(board) != 0 or len(get_empty_cells(board)) == 0
    
    def evaluate(board):
        """Evaluate the board position"""
        winner = get_winner(board)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        else:
            return 0
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0 or is_terminal(board):
            return evaluate(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for z, y, x in get_empty_cells(board):
                board[z][y][x] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for z, y, x in get_empty_cells(board):
                board[z][y][x] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate winning moves
    for z, y, x in get_empty_cells(board):
        board[z][y][x] = 1
        if get_winner(board) == 1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
    
    # Check for blocking opponent's winning moves
    for z, y, x in get_empty_cells(board):
        board[z][y][x] = -1
        if get_winner(board) == -1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
    
    # If center is available, take it
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Use minimax for the best move
    best_score = float('-inf')
    best_move = None
    
    for z, y, x in get_empty_cells(board):
        board[z][y][x] = 1
        score = minimax(board, 5, float('-inf'), float('inf'), False)
        board[z][y][x] = 0
        
        if score > best_score:
            best_score = score
            best_move = (z, y, x)
    
    # Fallback to first available move if no best move found
    if best_move is None:
        empty_cells = get_empty_cells(board)
        if empty_cells:
            best_move = empty_cells[0]
    
    return best_move
