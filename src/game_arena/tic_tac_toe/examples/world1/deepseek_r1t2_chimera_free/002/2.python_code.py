
def policy(board: list[list[int]]) -> tuple[int, int]:
    def evaluate(board: list[list[int]]) -> None:
        # Check rows for winner
        for row in board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]

        # Check columns for winner
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != 0:
                return board[0][col]

        # Check diagonals for winner
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]

        # Check for draw (no empty cells left)
        if all(cell != 0 for row in board for cell in row):
            return 0

        # Game still ongoing
        return None

    def get_empty_cells(board: list[list[int]]) -> list[tuple[int, int]]:
        return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    def minimax(board: list[list[int]], maximizing: bool, alpha: float, beta: float) -> float:
        result = evaluate(board)
        if result is not None:
            if result == 1:
                return 1
            elif result == -1:
                return -1
            return 0

        empty_cells = get_empty_cells(board)
        if maximizing:
            max_eval = -float('inf')
            for r, c in empty_cells:
                board[r][c] = 1
                eval = minimax(board, False, alpha, beta)
                board[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                board[r][c] = -1
                eval = minimax(board, True, alpha, beta)
                board[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Check for empty board and start with center if possible
    if all(cell == 0 for row in board for cell in row):
        return (1, 1)

    # Check immediate win for AI
    empty_cells = get_empty_cells(board)
    for r, c in empty_cells:
        board[r][c] = 1
        if evaluate(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Check immediate block for opponent
    for r, c in empty_cells:
        board[r][c] = -1
        if evaluate(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Use minimax to find best possible move
    best_score = -float('inf')
    best_move = empty_cells[0]  # fallback to first available move
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, False, -float('inf'), float('inf'))
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
            if best_score == 1:
                break  # winning move found, no need to check others

    return best_move
