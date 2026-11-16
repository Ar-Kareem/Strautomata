
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the player '1' using Minimax with Alpha-Beta pruning.
    
    Args:
        board: A 3x3 list of lists where 0 is empty, 1 is the player, and -1 is the opponent.
        
    Returns:
        A tuple (row, col) coordinates of the chosen move.
    """
    ME = 1
    OPPONENT = -1
    EMPTY = 0

    def get_winner(b):
        """Returns the winner ID (1 or -1) or None if no winner yet."""
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] and row[0] != EMPTY:
                return row[0]
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] and b[0][col] != EMPTY:
                return b[0][col]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] and b[0][0] != EMPTY:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] and b[0][2] != EMPTY:
            return b[0][2]
        return None

    def is_full(b):
        """Returns True if the board has no empty spots."""
        for row in b:
            for cell in row:
                if cell == EMPTY:
                    return False
        return True

    def minimax(b, depth, is_maximizing, alpha, beta):
        """
        Minimax recursive function with Alpha-Beta pruning.
        Returns the score of the board state.
        """
        winner = get_winner(b)
        if winner == ME:
            return 10 - depth
        if winner == OPPONENT:
            return depth - 10
        if is_full(b):
            return 0

        if is_maximizing:
            max_eval = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == EMPTY:
                        b[r][c] = ME
                        eval_val = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = EMPTY
                        max_eval = max(max_eval, eval_val)
                        alpha = max(alpha, eval_val)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == EMPTY:
                        b[r][c] = OPPONENT
                        eval_val = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = EMPTY
                        min_eval = min(min_eval, eval_val)
                        beta = min(beta, eval_val)
                        if beta <= alpha:
                            break
            return min_eval

    # Move ordering optimization: Center -> Corners -> Edges
    # This helps Alpha-Beta prune branches earlier.
    priority_moves = [
        (1, 1), 
        (0, 0), (0, 2), (2, 0), (2, 2), 
        (0, 1), (1, 0), (1, 2), (2, 1)
    ]
    
    best_score = -math.inf
    best_move = None
    
    # Iterate through valid moves finding the one with the highest score
    for r, c in priority_moves:
        if board[r][c] == EMPTY:
            board[r][c] = ME
            # Call minimax for the resulting state (opponent's turn to minimize)
            score = minimax(board, 0, False, -math.inf, math.inf)
            board[r][c] = EMPTY # Backtrack
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
                # If we found a guaranteed win (max score), we can stop searching.
                if best_score == 10:
                    break
    
    # Fallback if board is full or no moves (though game logic shouldn't call logic then)
    return best_move if best_move is not None else (0, 0)
