
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows
        for row in b:
            if sum(row) == 3:
                return 1
            if sum(row) == -3:
                return -1
        # Check columns
        for col in range(3):
            s = b[0][col] + b[1][col] + b[2][col]
            if s == 3:
                return 1
            if s == -3:
                return -1
        # Check diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d1 == 3 or d2 == 3:
            return 1
        if d1 == -3 or d2 == -3:
            return -1
        return 0
    
    def get_empty_cells(b):
        cells = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    cells.append((i, j))
        return cells
    
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth  # Prefer faster wins
        if winner == -1:
            return depth - 10  # Prefer slower losses
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = float('-inf')
            for (r, c) in empty:
                b[r][c] = 1
                eval_score = minimax(b, depth + 1, False, alpha, beta)
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
                eval_score = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Make a copy to avoid modifying original
    board_copy = [row[:] for row in board]
    
    # Find the best move
    empty_cells = get_empty_cells(board_copy)
    
    if not empty_cells:
        return (0, 0)  # Should not happen in a valid game
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for (r, c) in empty_cells:
        board_copy[r][c] = 1
        score = minimax(board_copy, 1, False, float('-inf'), float('inf'))
        board_copy[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
