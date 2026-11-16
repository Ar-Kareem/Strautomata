
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Computes the optimal next move for player 1 on a 3x3 Tic Tac Toe board.
    
    Args:
        board: 3x3 list of lists, where:
                0  = empty cell
                1  = our move
               -1  = opponent's move

    Returns:
        tuple[int, int]: (row, col) coordinates of the chosen empty cell.
    """
    # Preferred order of cells for alpha-beta pruning efficiency:
    # Center, corners, then edges
    MOVE_ORDER = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (1, 2), (2, 1)
    ]

    def check_winner(b: list[list[int]]) -> int:
        """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
        # Check rows and columns
        for i in range(3):
            if b[i][0] != 0 and b[i][0] == b[i][1] == b[i][2]:
                return b[i][0]
            if b[0][i] != 0 and b[0][i] == b[1][i] == b[2][i]:
                return b[0][i]

        # Check diagonals
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2]:
            return b[0][0]
        if b[0][2] != 0 and b[0][2] == b[1][1] == b[2][0]:
            return b[0][2]

        return 0

    def minimax(b: list[list[int]], is_maximizing: bool, depth: int, alpha: float, beta: float) -> int:
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10

        # Check for draw
        empty_cells = [(r, c) for r, c in MOVE_ORDER if b[r][c] == 0]
        if not empty_cells:
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in empty_cells:
                b[r][c] = 1
                eval_score = minimax(b, False, depth + 1, alpha, beta)
                b[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                b[r][c] = -1
                eval_score = minimax(b, True, depth + 1, alpha, beta)
                b[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    best_score = -float('inf')
    best_move = None

    # Work with a shallow copy of rows to prevent external state mutation
    working_board = [row[:] for row in board]
    available_moves = [(r, c) for r, c in MOVE_ORDER if working_board[r][c] == 0]

    if not available_moves:
        return (0, 0)

    # Fast-path: Win immediately if a winning move is directly available
    for r, c in available_moves:
        working_board[r][c] = 1
        if check_winner(working_board) == 1:
            return (r, c)
        working_board[r][c] = 0

    # Fast-path: Block opponent's immediate winning move
    for r, c in available_moves:
        working_board[r][c] = -1
        if check_winner(working_board) == -1:
            return (r, c)
        working_board[r][c] = 0

    # Search for the optimal move
    alpha = -float('inf')
    beta = float('inf')

    for r, c in available_moves:
        working_board[r][c] = 1
        move_score = minimax(working_board, False, 0, alpha, beta)
        working_board[r][c] = 0

        if move_score > best_score:
            best_score = move_score
            best_move = (r, c)

        alpha = max(alpha, best_score)

    return best_move if best_move is not None else available_moves[0]
