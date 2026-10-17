
def policy(board: list[list[int]]) -> int:
    """
    Returns the best move for the current player (1) on the board.
    Uses minimax algorithm with alpha-beta pruning.
    """
    
    def check_winner(b):
        """Check if there's a winner. Returns 1, -1, or 0."""
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
    
    def is_full(b):
        """Check if board is full."""
        return all(b[i][j] != 0 for i in range(3) for j in range(3))
    
    def minimax(b, is_maximizing, alpha, beta):
        """Minimax with alpha-beta pruning."""
        winner = check_winner(b)
        if winner != 0:
            return winner
        if is_full(b):
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval = minimax(b, False, alpha, beta)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval = minimax(b, True, alpha, beta)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False, -float('inf'), float('inf'))
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = i * 3 + j + 1
    
    # If no move found (shouldn't happen), return first available
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return i * 3 + j + 1
    
    return best_move
