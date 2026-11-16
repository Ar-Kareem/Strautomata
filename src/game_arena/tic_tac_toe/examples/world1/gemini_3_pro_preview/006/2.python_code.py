
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the optimal move for Player 1 (Self) in a 3x3 Tic Tac Toe game.
    
    Args:
        board: A 3x3 list of lists where 0 is empty, 1 is self, -1 is opponent.
    
    Returns:
        A tuple (row, col) representing the chosen move.
    """
    
    # ---------------- Helper Functions ----------------

    def check_status(b):
        """
        Checks the board status.
        Returns:
            1 if Player 1 won,
            -1 if Player -1 won,
            0 otherwise (draw or ongoing)
        """
        # Check Rows and Columns
        for i in range(3):
            # Check Row i
            if abs(sum(b[i])) == 3:
                return b[i][0]
            # Check Col i
            col_sum = b[0][i] + b[1][i] + b[2][i]
            if abs(col_sum) == 3:
                return b[0][i]
        
        # Check Diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        d2 = b[0][2] + b[1][1] + b[2][0]
        if abs(d1) == 3: return b[1][1]
        if abs(d2) == 3: return b[1][1]
        
        return 0

    def get_legal_moves(b):
        """Returns a list of (r, c) tuples for all empty cells."""
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def minimax(b, depth, is_maximizing, alpha, beta):
        """
        Minimax with Alpha-Beta pruning to find board value.
        Scores: +10 for win, -10 for loss, adjusted by depth to prefer fast wins.
        """
        winner = check_status(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10
        
        moves = get_legal_moves(b)
        if not moves:
            return 0  # Draw

        if is_maximizing:
            max_eval = -1000
            for r, c in moves:
                b[r][c] = 1
                eval_val = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = 0
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 1000
            for r, c in moves:
                b[r][c] = -1
                eval_val = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = 0
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # ---------------- Main Logic ----------------

    legal_moves = get_legal_moves(board)

    # If no legal moves, return a safe default (though game should be over)
    if not legal_moves:
        return (0, 0)

    # Optimization: On an empty board, the center is the best opening
    if len(legal_moves) == 9:
        return (1, 1)

    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Initialize alpha-beta bounds
    alpha = -float('inf')
    beta = float('inf')

    # Iterate through all legal moves to find the one with the highest Minimax value
    for r, c in legal_moves:
        board[r][c] = 1
        # Call minimax for the resulting state (depth 0 relative to search, next is opponent)
        score = minimax(board, 0, False, alpha, beta)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        # Update alpha for the maximization step at the root
        alpha = max(alpha, score)

    return best_move
