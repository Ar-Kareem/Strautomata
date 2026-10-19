
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy using minimax with alpha-beta pruning.
    Returns the best move as (row, col).
    """
    
    def check_winner(b):
        """Check if there's a winner. Returns 1, -1, or 0."""
        # Check rows
        for row in b:
            if abs(sum(row)) == 4:
                return row[0]
        
        # Check columns
        for col in range(4):
            s = sum(b[row][col] for row in range(4))
            if abs(s) == 4:
                return b[0][col]
        
        # Check diagonals
        diag1 = sum(b[i][i] for i in range(4))
        if abs(diag1) == 4:
            return b[0][0]
        
        diag2 = sum(b[i][3-i] for i in range(4))
        if abs(diag2) == 4:
            return b[0][3]
        
        return 0
    
    def is_full(b):
        """Check if board is full."""
        return all(b[i][j] != 0 for i in range(4) for j in range(4))
    
    def evaluate(b):
        """Evaluate board position."""
        winner = check_winner(b)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        return 0
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        """Minimax with alpha-beta pruning."""
        score = evaluate(b)
        
        # Terminal states
        if score == 1000:
            return score - depth
        if score == -1000:
            return score + depth
        if is_full(b):
            return 0
        
        # Depth limit for performance
        if depth >= 6:
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval_score = minimax(b, depth + 1, alpha, beta, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval_score = minimax(b, depth + 1, alpha, beta, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    best_score = -float('inf')
    best_move = None
    
    # Try center positions first (better heuristic)
    move_order = [(1,1), (1,2), (2,1), (2,2), (0,0), (0,3), (3,0), (3,3),
                  (0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    
    for i, j in move_order:
        if board[i][j] == 0:
            board[i][j] = 1
            score = minimax(board, 0, -float('inf'), float('inf'), False)
            board[i][j] = 0
            
            if score > best_score:
                best_score = score
                best_move = (i, j)
    
    # Fallback: return first available move
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
