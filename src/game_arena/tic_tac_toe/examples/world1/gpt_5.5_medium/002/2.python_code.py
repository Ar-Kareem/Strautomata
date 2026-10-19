
from typing import List, Tuple

Board = List[List[int]]


def policy(board: Board) -> Tuple[int, int]:
    """
    Return the best legal move for the player represented by 1.
    The opponent is represented by -1.
    Empty cells are represented by 0.
    """

    legal = _legal_moves(board)
    if not legal:
        # This should not happen in a valid non-terminal game.
        # Return a valid-shaped fallback.
        return (0, 0)

    best_score = float("-inf")
    best_move = legal[0]

    for r, c in _ordered_moves(legal):
        board[r][c] = 1
        score = _minimax(board, maximizing=False, depth=1, alpha=float("-inf"), beta=float("inf"))
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move


def _minimax(board: Board, maximizing: bool, depth: int, alpha: float, beta: float) -> int:
    winner = _winner(board)

    if winner == 1:
        return 100 - depth
    if winner == -1:
        return depth - 100

    legal = _legal_moves(board)
    if not legal:
        return 0

    if maximizing:
        best = float("-inf")
        for r, c in _ordered_moves(legal):
            board[r][c] = 1
            score = _minimax(board, maximizing=False, depth=depth + 1, alpha=alpha, beta=beta)
            board[r][c] = 0

            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break

        return int(best)

    else:
        best = float("inf")
        for r, c in _ordered_moves(legal):
            board[r][c] = -1
            score = _minimax(board, maximizing=True, depth=depth + 1, alpha=alpha, beta=beta)
            board[r][c] = 0

            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break

        return int(best)


def _winner(board: Board) -> int:
    lines = []

    # Rows
    lines.extend(board)

    # Columns
    for c in range(3):
        lines.append([board[0][c], board[1][c], board[2][c]])

    # Diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        s = sum(line)
        if s == 3:
            return 1
        if s == -3:
            return -1

    return 0


def _legal_moves(board: Board) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]


def _ordered_moves(moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    preferred = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (1, 2), (2, 1),
    ]
    move_set = set(moves)
    return [m for m in preferred if m in move_set]
