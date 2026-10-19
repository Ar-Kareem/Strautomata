
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
            return 10 - depth  # Prefer faster wins
        if winner == -1:  # Opponent wins
            return depth - 10  # Prefer slower losses
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = float('-inf')
            for (i, j) in empty:
                b[i][j] = 1
                eval_score = minimax(b, False, alpha, beta, depth + 1)
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
                eval_score = minimax(b, True, alpha, beta, depth + 1)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move for player 1 (me)
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        return (0, 0)  # Shouldn't happen in a valid game
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for (i, j) in empty_cells:
        board[i][j] = 1
        score = minimax(board, False, float('-inf'), float('inf'), 1)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
