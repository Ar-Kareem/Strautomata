
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows
        for row in b:
            s = sum(row)
            if s == 3:
                return 1
            if s == -3:
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
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]
    
    def minimax(b, is_maximizing, depth, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth  # Prefer quicker wins
        if winner == -1:
            return depth - 10  # Prefer slower losses
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw
        
        if is_maximizing:
            best = -float('inf')
            for (i, j) in empty:
                b[i][j] = 1
                score = minimax(b, False, depth + 1, alpha, beta)
                b[i][j] = 0
                best = max(best, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for (i, j) in empty:
                b[i][j] = -1
                score = minimax(b, True, depth + 1, alpha, beta)
                b[i][j] = 0
                best = min(best, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return best
    
    # Find the best move for player 1 (me)
    best_score = -float('inf')
    best_move = None
    
    empty_cells = get_empty_cells(board)
    
    # If board is empty, take center
    if len(empty_cells) == 9:
        return (1, 1)
    
    for (i, j) in empty_cells:
        board[i][j] = 1
        score = minimax(board, False, 1, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
