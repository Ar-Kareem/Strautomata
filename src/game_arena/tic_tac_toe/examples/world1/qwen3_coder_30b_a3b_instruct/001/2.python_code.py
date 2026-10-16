
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_game_over(board):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != 0:
                return board[i][0]
            if board[0][i] == board[1][i] == board[2][i] != 0:
                return board[0][i]
        
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        
        # Check for draw (no empty spaces left)
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return 0  # Game not over
        return 0  # Draw
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        winner = is_game_over(board)
        if winner == 1:  # AI wins
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif winner == 0:  # Draw
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        eval_score = minimax(board, depth + 1, False, alpha, beta)
                        board[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        eval_score = minimax(board, depth + 1, True, alpha, beta)
                        board[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Try to win or block opponent first
    # Check if we can win in one move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if is_game_over(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check if opponent can win in one move and block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if is_game_over(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Otherwise use minimax to find best move
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, float('-inf'), float('inf'))
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    if best_move is None:
        # Fallback: find first empty spot
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
