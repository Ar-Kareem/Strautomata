
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the optimal move (row, col) for the current player (1)
    using Minimax with Alpha-Beta pruning.
    
    Start state: 'board' contains 0 (empty), 1 (player), -1 (opponent).
    """
    
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0

    def check_winner(b):
        """
        Returns 1 if Player wins, -1 if Opponent wins, 0 otherwise.
        Prioritizes checking lines for wins.
        """
        # Check rows
        for row in b:
            s = sum(row)
            if s == 3: return PLAYER
            if s == -3: return OPPONENT
        
        # Check columns
        for c in range(3):
            s = b[0][c] + b[1][c] + b[2][c]
            if s == 3: return PLAYER
            if s == -3: return OPPONENT
            
        # Check diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d1 == 3 or d2 == 3: return PLAYER
        if d1 == -3 or d2 == -3: return OPPONENT
        
        return 0

    def get_valid_moves(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == EMPTY]

    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == PLAYER:
            return 10 - depth
        if winner == OPPONENT:
            return depth - 10
        
        moves = get_valid_moves(b)
        if not moves:
            return 0  # Draw

        if is_maximizing:
            max_eval = -math.inf
            for r, c in moves:
                b[r][c] = PLAYER
                eval_val = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = EMPTY
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
                b[r][c] = EMPTY
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Get all possible moves
    possible_moves = get_valid_moves(board)

    # Optimization: If board is empty, take center.
    if len(possible_moves) == 9:
        return (1, 1)
    
    # Fallback if board is full (should not happen in standard gameplay flow)
    if not possible_moves:
        return (0, 0)

    best_move = possible_moves[0]
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf

    # Iterate through moves to find the one that maximizes the Minimax value
    for r, c in possible_moves:
        board[r][c] = PLAYER
        # After we move, it's the opponent's turn (minimize)
        move_val = minimax(board, 0, False, alpha, beta)
        board[r][c] = EMPTY # Backtrack

        if move_val > best_value:
            best_value = move_val
            best_move = (r, c)
        
        alpha = max(alpha, best_value)
        # Note: We don't prune at the root level because we want to ensure
        # we pick the absolute best move, not just "a" good move that satisfies alpha.
    
    return best_move
