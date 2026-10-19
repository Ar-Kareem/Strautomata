
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper to check for a winner: return 1 if me wins, -1 if opponent, 0 otherwise
    def evaluate(board):
        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] and row[0] != 0:
                return row[0]
        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] and board[0][col] != 0:
                return board[0][col]
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
            return board[0][2]
        return 0  # No winner
    
    # Helper to check if board is full
    def is_full(board):
        return all(cell != 0 for row in board for cell in row)
    
    # Minimax with alpha-beta pruning
    def minimax(board, depth, is_maximizing, alpha, beta):
        score = evaluate(board)
        if score != 0:
            return score - depth if score == 1 else score + depth  # Favor quicker wins
        if is_full(board):
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1  # My move
                        eval = minimax(board, depth + 1, False, alpha, beta)
                        board[i][j] = 0  # Undo
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1  # Opponent's move
                        eval = minimax(board, depth + 1, True, alpha, beta)
                        board[i][j] = 0  # Undo
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find the best move
    best_val = float('-inf')
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1  # My move
                move_val = minimax(board, 0, False, float('-inf'), float('inf'))
                board[i][j] = 0  # Undo
                if move_val > best_val:
                    best_val = move_val
                    best_move = (i, j)
    
    return best_move  # Guaranteed to be legal since we only check empty cells
