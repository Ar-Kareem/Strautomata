
def policy(board: list[list[int]]) -> tuple[int, int]:
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
    
    def get_empty_cells(b):
        cells = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    cells.append((i, j))
        return cells
    
    def minimax(b, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 1
        if winner == -1:
            return -1
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = -float('inf')
            for (i, j) in empty:
                b[i][j] = 1
                eval_score = minimax(b, False, alpha, beta)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (i, j) in empty:
                b[i][j] = -1
                eval_score = minimax(b, True, alpha, beta)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    best_move = None
    best_score = -float('inf')
    
    empty_cells = get_empty_cells(board)
    
    # If board is empty, play center or corner for optimal play
    if len(empty_cells) == 9:
        return (1, 1)
    
    for (i, j) in empty_cells:
        board[i][j] = 1
        score = minimax(board, False, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
