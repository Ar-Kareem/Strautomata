
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Analyzes the Tic Tac Toe board and returns the optimal move for player 1.
    Uses Minimax algorithm with Alpha-Beta pruning.
    
    Args:
        board: A 3x3 list of lists containing 0 (empty), 1 (you), -1 (opponent).
        
    Returns:
        (row, col): The coordinates of the chosen move.
    """
    
    # Constants
    ME = 1
    OPPONENT = -1
    EMPTY = 0
    
    # helper to find all valid move coordinates
    def get_available_moves(b):
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    # helper to check if a player has won
    def get_winner(b):
        # Rows
        for row in b:
            s = sum(row)
            if s == 3: return ME
            if s == -3: return OPPONENT
        
        # Cols
        for c in range(3):
            s = b[0][c] + b[1][c] + b[2][c]
            if s == 3: return ME
            if s == -3: return OPPONENT
            
        # Diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        if d1 == 3: return ME
        if d1 == -3: return OPPONENT
        
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d2 == 3: return ME
        if d2 == -3: return OPPONENT
        
        return None

    # recursive minimax with alpha-beta pruning
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = get_winner(b)
        
        # Terminal states with depth scoring
        # Prefer winning sooner (higher score) and losing later (lower negative score)
        if winner == ME:
            return 10 - depth
        if winner == OPPONENT:
            return depth - 10
        
        moves = get_available_moves(b)
        if not moves:
            return 0 # Draw

        if is_maximizing:
            max_eval = -math.inf
            for r, c in moves:
                b[r][c] = ME
                eval_val = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = EMPTY # Backtrack
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                b[r][c] = OPPONENT
                eval_val = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = EMPTY # Backtrack
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Policy Logic ---
    
    available = get_available_moves(board)
    
    # Optimization: If board is empty, take center immediately
    if len(available) == 9:
        return (1, 1)

    best_move = available[0]
    best_value = -math.inf
    
    # Iterate through all available moves to find the one with the highest minimax value
    # Alpha is initialized to -inf, Beta to +inf
    alpha = -math.inf
    beta = math.inf
    
    for r, c in available:
        board[r][c] = ME
        # Next turn is opponent's (minimizing)
        move_value = minimax(board, 0, False, alpha, beta)
        board[r][c] = EMPTY # Backtrack
        
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
            
        # Update alpha for the root level optimization
        alpha = max(alpha, best_value)
        
    return best_move
