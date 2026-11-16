
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy using minimax with alpha-beta pruning.
    Returns the best move as (row, col).
    """
    
    def check_winner(b):
        """Check if there's a winner. Returns 1, -1, or 0."""
        # Check rows
        for row in b:
            if all(cell == 1 for cell in row):
                return 1
            if all(cell == -1 for cell in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(b[row][col] == 1 for row in range(4)):
                return 1
            if all(b[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(b[i][i] == 1 for i in range(4)):
            return 1
        if all(b[i][i] == -1 for i in range(4)):
            return -1
        if all(b[i][3-i] == 1 for i in range(4)):
            return 1
        if all(b[i][3-i] == -1 for i in range(4)):
            return -1
        
        return 0
    
    def is_terminal(b):
        """Check if game is over."""
        if check_winner(b) != 0:
            return True
        return all(b[i][j] != 0 for i in range(4) for j in range(4))
    
    def evaluate(b):
        """Evaluate board state."""
        winner = check_winner(b)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        return 0
    
    def get_moves(b):
        """Get all valid moves."""
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def minimax(b, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0 or is_terminal(b):
            return evaluate(b)
        
        if maximizing:
            max_eval = float('-inf')
            for move in get_moves(b):
                i, j = move
                b[i][j] = 1
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in get_moves(b):
                i, j = move
                b[i][j] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Count filled positions to determine search depth
    filled = sum(1 for i in range(4) for j in range(4) if board[i][j] != 0)
    
    # Adjust depth based on game stage
    if filled < 4:
        depth = 6
    elif filled < 8:
        depth = 8
    else:
        depth = 16  # Search to end in late game
    
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    for move in get_moves(board):
        i, j = move
        board[i][j] = 1
        score = minimax(board, depth - 1, alpha, beta, False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)
    
    return best_move if best_move else (0, 0)
