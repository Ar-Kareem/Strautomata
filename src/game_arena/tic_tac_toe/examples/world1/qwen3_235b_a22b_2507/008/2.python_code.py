
def policy(board: list[list[int]]) -> tuple[int, int]:
    def evaluate(board):
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
        
        # Game not over or draw
        return 0
    
    def is_terminal(board):
        # Check if game is over (win or draw)
        if evaluate(board) != 0:
            return True
        
        # Check for empty squares
        for row in board:
            if 0 in row:
                return False
        return True
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        score = evaluate(board)
        
        # Return scores for terminal states
        if score == 1:  # I win
            return 10 - depth
        if score == -1:  # Opponent wins
            return depth - 10
        if is_terminal(board):  # Draw
            return 0
            
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1  # My move
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i][j] = 0  # Undo move
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
                        board[i][j] = -1  # Opponent's move
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i][j] = 0  # Undo move
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_move = (0, 0)
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1  # Try my move
                move_score = minimax(board, 0, float('-inf'), float('inf'), False)
                board[i][j] = 0  # Undo move
                
                if move_score > best_score:
                    best_score = move_score
                    best_move = (i, j)
    
    return best_move
