
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Computes the optimal move for player 1 using Minimax with Alpha-Beta pruning.
    
    Args:
        board: 3x3 list of lists, where 0 is empty, 1 is our piece, -1 is opponent's piece.
        
    Returns:
        (row, col) tuple representing the chosen legal move.
    """
    # Priority ordering for tie-breaking: center, corners, edges
    move_priority = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]

    def check_winner(b: list[list[int]]) -> int:
        # Check rows and columns
        for i in range(3):
            row_sum = b[i][0] + b[i][1] + b[i][2]
            if row_sum == 3:
                return 1
            if row_sum == -3:
                return -1
            
            col_sum = b[0][i] + b[1][i] + b[2][i]
            if col_sum == 3:
                return 1
            if col_sum == -3:
                return -1

        # Check diagonals
        diag1 = b[0][0] + b[1][1] + b[2][2]
        if diag1 == 3:
            return 1
        if diag1 == -3:
            return -1

        diag2 = b[0][2] + b[1][1] + b[2][0]
        if diag2 == 3:
            return 1
        if diag2 == -3:
            return -1

        return 0

    def get_empty_cells(b: list[list[int]]) -> list[tuple[int, int]]:
        cells = []
        for r, c in move_priority:
            if b[r][c] == 0:
                cells.append((r, c))
        return cells

    def minimax(b: list[list[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return -10 + depth

        empty_cells = get_empty_cells(b)
        if not empty_cells:
            return 0  # Draw

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in empty_cells:
                b[r][c] = 1
                ev = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = 0
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                b[r][c] = -1
                ev = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = 0
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval

    legal_moves = get_empty_cells(board)
    if not legal_moves:
        return (0, 0)

    best_score = -float('inf')
    best_move = legal_moves[0]

    for r, c in legal_moves:
        board[r][c] = 1
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
