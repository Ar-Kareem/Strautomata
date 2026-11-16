
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Optimal Tic Tac Toe policy using minimax algorithm.
    Returns the best move for player 1.
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
    
    def minimax(b, is_maximizing):
        """Minimax algorithm with alpha-beta pruning."""
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
                        eval_score = minimax(b, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval_score = minimax(b, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
            return min_eval
    
    # Find the best move
    best_score = -float('inf')
    best_move = None
    
    # Try each empty cell
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try this move
                board[i][j] = 1
                score = minimax(board, False)
                board[i][j] = 0
                
                # Update best move
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # If no move found (shouldn't happen), return first empty cell
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
