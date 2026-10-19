
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != 0:
                return board[0][col]
        
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        
        return 0  # No winner
    
    def is_full(board):
        return all(board[i][j] != 0 for i in range(3) for j in range(3))
    
    def get_empty_cells(board):
        return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        winner = check_winner(board)
        
        # Terminal states
        if winner == 1:  # AI wins
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return -10 + depth
        elif is_full(board):  # Draw
            return 0
        
        empty_cells = get_empty_cells(board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for row, col in empty_cells:
                board[row][col] = 1
                eval_score = minimax(board, depth + 1, False, alpha, beta)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in empty_cells:
                board[row][col] = -1
                eval_score = minimax(board, depth + 1, True, alpha, beta)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_move = None
    empty_cells = get_empty_cells(board)
    
    for row, col in empty_cells:
        board[row][col] = 1
        score = minimax(board, 0, False, float('-inf'), float('inf'))
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move if best_move else (0, 0)
