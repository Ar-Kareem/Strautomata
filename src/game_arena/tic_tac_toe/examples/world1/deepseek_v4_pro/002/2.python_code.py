
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the optimal move for player 1 using minimax with alpha-beta pruning.
    """
    # Find all empty cells
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if not empty:
        return (0, 0)  # fallback, should not happen

    best_score = -float('inf')
    best_move = empty[0]

    # Try each possible move, run minimax, pick the best
    for i, j in empty:
        board[i][j] = 1
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)

    return best_move


def minimax(board: list[list[int]], depth: int, is_maximizing: bool,
            alpha: float, beta: float) -> float:
    """
    Minimax with alpha-beta pruning.
    """
    winner = check_winner(board)
    if winner == 1:
        return 10 - depth  # prefer quicker win
    if winner == -1:
        return -10 + depth  # prefer slower loss
    if is_board_full(board):
        return 0

    if is_maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_ = minimax(board, depth + 1, False, alpha, beta)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_)
                    alpha = max(alpha, eval_)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_ = minimax(board, depth + 1, True, alpha, beta)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_)
                    beta = min(beta, eval_)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval


def check_winner(board: list[list[int]]) -> int:
    """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    # Rows and columns
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != 0:
            return board[0][i]
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return 0


def is_board_full(board: list[list[int]]) -> bool:
    """Returns True if no empty cells remain."""
    for row in board:
        if 0 in row:
            return False
    return True
