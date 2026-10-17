
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the optimal move for Player 1 (AI) using Minimax with Alpha-Beta pruning.
    
    Args:
        board: A 3x3 list of lists where 0 is empty, 1 is self, and -1 is opponent.
        
    Returns:
        A tuple (row, col) representing the next move.
    """
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0

    def check_winner(b):
        """Returns the winner (1 or -1) or 0 if no winner yet."""
        # Check Rows & Columns
        for i in range(3):
            # Row i
            s_row = b[i][0] + b[i][1] + b[i][2]
            if s_row == 3: return PLAYER
            if s_row == -3: return OPPONENT
            # Col i
            s_col = b[0][i] + b[1][i] + b[2][i]
            if s_col == 3: return PLAYER
            if s_col == -3: return OPPONENT
            
        # Check Diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        if d1 == 3: return PLAYER
        if d1 == -3: return OPPONENT
        
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d2 == 3: return PLAYER
        if d2 == -3: return OPPONENT
        
        return 0

    def is_full(b):
        """Returns True if there are no empty cells left."""
        for r in range(3):
            for c in range(3):
                if b[r][c] == EMPTY:
                    return False
        return True

    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == PLAYER:
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
                        b[r][c] = PLAYER
                        eval_score = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = EMPTY
                        
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            return max_eval # Beta cutoff
            return max_eval
        else:
            min_eval = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == EMPTY:
                        b[r][c] = OPPONENT
                        eval_score = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = EMPTY
                        
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            return min_eval # Alpha cutoff
            return min_eval

    # Get valid moves
    valid_moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == EMPTY:
                valid_moves.append((r, c))

    # Fallback if board is full (should not happen in policy call)
    if not valid_moves:
        return (0, 0)

    # Heuristic: If board is empty, take center immediately
    if len(valid_moves) == 9:
        return (1, 1)

    best_score = -math.inf
    best_move = valid_moves[0]

    for (r, c) in valid_moves:
        board[r][c] = PLAYER
        score = minimax(board, 0, False, -math.inf, math.inf)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            # If we found a winning move, return immediately
            if best_score > 0: 
                # Theoretically 10 is max (immediate win), but >0 guarantees a forced win path
                pass

    return best_move
