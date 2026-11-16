
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows, columns, and diagonals
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0:
                return b[0][i]
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
    
    def minimax(b, is_maximizing, alpha, beta, depth):
        winner = check_winner(b)
        if winner == 1:  # I win
            return 10 - depth  # Prefer winning sooner
        if winner == -1:  # Opponent wins
            return -10 + depth  # Prefer losing later
        
        empty = get_empty_cells(b)
        if not empty:  # Draw
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for (r, c) in empty:
                b[r][c] = 1
                eval_score = minimax(b, False, alpha, beta, depth + 1)
                b[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (r, c) in empty:
                b[r][c] = -1
                eval_score = minimax(b, True, alpha, beta, depth + 1)
                b[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Make a copy of the board to avoid modifying the original
    b = [row[:] for row in board]
    
    # Find the best move
    best_move = None
    best_score = float('-inf')
    
    empty_cells = get_empty_cells(b)
    
    # If board is empty, play center (optimal first move)
    if len(empty_cells) == 9:
        return (1, 1)
    
    for (r, c) in empty_cells:
        b[r][c] = 1
        score = minimax(b, False, float('-inf'), float('inf'), 0)
        b[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
