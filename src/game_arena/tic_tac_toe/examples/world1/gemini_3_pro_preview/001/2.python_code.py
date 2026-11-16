
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Computes the optimal move for a 3x3 Tic-Tac-Toe game using Minimax with Alpha-Beta pruning.
    1 is the AI (Maximizing), -1 is Opponent (Minimizing), 0 is Empty.
    """
    
    ME = 1
    OPPONENT = -1
    EMPTY = 0

    def get_winner(b):
        """Returns the winner ID (1 or -1) if one exists, else None."""
        # Check rows and columns
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != EMPTY:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != EMPTY:
                return b[0][i]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != EMPTY:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != EMPTY:
            return b[0][2]
        return None

    def is_full(b):
        """Returns True if no empty cells remain."""
        for r in range(3):
            for c in range(3):
                if b[r][c] == EMPTY:
                    return False
        return True

    def minimax(b, depth, is_maximizing, alpha, beta):
        """
        Recursive minimax search to evaluate board state.
        Returns a score: positive for AI win, negative for opponent win, 0 for draw.
        """
        winner = get_winner(b)
        if winner == ME:
            return 10 - depth
        if winner == OPPONENT:
            return depth - 10
        if is_full(b):
            return 0

        # Prioritize moves: Center -> Corners -> Edges to improve pruning
        preference = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
        candidates = []
        for r, c in preference:
            if b[r][c] == EMPTY:
                candidates.append((r, c))

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in candidates:
                b[r][c] = ME
                eval_score = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = EMPTY # Backtrack
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in candidates:
                b[r][c] = OPPONENT
                eval_score = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = EMPTY # Backtrack
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Policy Logic ---
    
    # Identify valid moves ordered by heuristic preference
    possible_moves = []
    preference_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in preference_order:
        if board[r][c] == EMPTY:
            possible_moves.append((r, c))

    if not possible_moves:
        return (0, 0) # Fallback if board is full

    best_score = -float('inf')
    best_move = possible_moves[0]

    for r, c in possible_moves:
        board[r][c] = ME
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[r][c] = EMPTY # Backtrack

        if score > best_score:
            best_score = score
            best_move = (r, c)
            # If we found an immediate winning path, take it.
            if best_score == 10:
                break

    return best_move
