
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Uses minimax algorithm with alpha-beta pruning to find optimal move.
    """
    # Make a copy to avoid modifying the original
    board = [row[:] for row in board]
    
    def check_winner(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] != 0:
                return b[0][col]
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        
        return 0
    
    def is_full(b):
        for row in b:
            if 0 in row:
                return False
        return True
    
    def get_empty_cells(b):
        empty = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        elif winner == -1:
            return -10 + depth
        elif is_full(b):
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i, j in get_empty_cells(b):
                b[i][j] = 1
                eval = minimax(b, depth + 1, False, alpha, beta)
                b[i][j] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in get_empty_cells(b):
                b[i][j] = -1
                eval = minimax(b, depth + 1, True, alpha, beta)
                b[i][j] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get all empty cells
    empty_cells = get_empty_cells(board)
    
    # Safety check
    if not empty_cells:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)
    
    # Find best move using minimax
    best_score = -float('inf')
    best_move = empty_cells[0]
    
    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
