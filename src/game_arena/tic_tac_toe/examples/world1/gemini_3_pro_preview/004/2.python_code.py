
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the player '1' in a Tic Tac Toe game using Minimax.
    """
    PLAYER = 1
    OPPONENT = -1

    def get_winner(b):
        """Returns 1 if player wins, -1 if opponent wins, 0 otherwise."""
        # Check rows
        for r in range(3):
            row_sum = sum(b[r])
            if row_sum == 3: return PLAYER
            if row_sum == -3: return OPPONENT
        
        # Check columns
        for c in range(3):
            col_sum = b[0][c] + b[1][c] + b[2][c]
            if col_sum == 3: return PLAYER
            if col_sum == -3: return OPPONENT
            
        # Check diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        if d1 == 3: return PLAYER
        if d1 == -3: return OPPONENT
        
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d2 == 3: return PLAYER
        if d2 == -3: return OPPONENT
        
        return 0

    def is_full(b):
        """Returns True if the board contains no empty spaces."""
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = get_winner(b)
        if winner == PLAYER:
            return 10 - depth
        if winner == OPPONENT:
            return -10 + depth
        if is_full(b):
            return 0
        
        if is_maximizing:
            max_eval = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = PLAYER
                        eval = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            return max_eval
            return max_eval
        else:
            min_eval = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = OPPONENT
                        eval = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            return min_eval
            return min_eval

    best_move = None
    best_val = -math.inf
    
    # Iterate through all valid moves to find the optimal one
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = PLAYER
                # Call minimax for the resulting state (it will be opponent's turn)
                move_val = minimax(board, 0, False, -math.inf, math.inf)
                board[r][c] = 0
                
                if move_val > best_val:
                    best_val = move_val
                    best_move = (r, c)
    
    # Fallback if no move is found (e.g., board full), though likely unreachable in play
    return best_move if best_move is not None else (0, 0)
