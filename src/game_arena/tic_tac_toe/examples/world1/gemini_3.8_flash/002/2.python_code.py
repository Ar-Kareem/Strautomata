
import math

LINES = [
    # Rows
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # Columns
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # Diagonals
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

# Positional bonus for tie-breaking between moves with equal theoretical value
POSITION_BONUS = {
    (1, 1): 0.20,
    (0, 0): 0.10,
    (0, 2): 0.10,
    (2, 0): 0.10,
    (2, 2): 0.10,
    (0, 1): 0.00,
    (1, 0): 0.00,
    (1, 2): 0.00,
    (2, 1): 0.00,
}


def _check_winner(board: list[list[int]]) -> int:
    """Returns 1 if player 1 has won, -1 if player -1 has won, or 0 otherwise."""
    for line in LINES:
        total = board[line[0][0]][line[0][1]] + board[line[1][0]][line[1][1]] + board[line[2][0]][line[2][1]]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


def _minimax(
    board: list[list[int]],
    depth: int,
    is_maximizing: bool,
    alpha: float,
    beta: float,
) -> float:
    winner = _check_winner(board)
    if winner == 1:
        return 10.0 - depth
    if winner == -1:
        return -10.0 + depth

    empty_cells = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not empty_cells:
        return 0.0  # Draw

    if is_maximizing:
        max_eval = -math.inf
        for r, c in empty_cells:
            board[r][c] = 1
            eval_score = _minimax(board, depth + 1, False, alpha, beta)
            board[r][c] = 0
            if eval_score > max_eval:
                max_eval = eval_score
            if eval_score > alpha:
                alpha = eval_score
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in empty_cells:
            board[r][c] = -1
            eval_score = _minimax(board, depth + 1, True, alpha, beta)
            board[r][c] = 0
            if eval_score < min_eval:
                min_eval = eval_score
            if eval_score < beta:
                beta = eval_score
            if beta <= alpha:
                break
        return min_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Evaluates the current 3x3 Tic Tac Toe board and returns the optimal move (row, col).
    - 0 represents an empty cell.
    - 1 represents our move.
    - -1 represents the opponent's move.
    """
    legal_moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

    # If only one legal move remains, take it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Fast start: center is dominant if opening
    if len(legal_moves) == 9:
        return (1, 1)

    best_score = -math.inf
    best_move = legal_moves[0]

    for r, c in legal_moves:
        board[r][c] = 1
        score = _minimax(board, 0, False, -math.inf, math.inf)
        board[r][c] = 0

        # Incorporate positional tie-breaker
        total_score = score + POSITION_BONUS.get((r, c), 0.0)

        if total_score > best_score:
            best_score = total_score
            best_move = (r, c)

    return best_move
