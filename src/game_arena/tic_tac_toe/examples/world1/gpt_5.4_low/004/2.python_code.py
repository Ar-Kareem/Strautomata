
from typing import List, Tuple

WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

# Positional preference for tie-breaking among equally optimal moves.
# Center > corners > edges.
MOVE_PRIORITY = {
    (1, 1): 3,
    (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
    (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
}


def _winner(board: List[List[int]]) -> int:
    for line in WIN_LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    cells = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    # Stronger tie-breaking by exploring best-looking moves first.
    cells.sort(key=lambda mv: MOVE_PRIORITY[mv], reverse=True)
    return cells


def _terminal_value(board: List[List[int]], depth: int) -> int | None:
    w = _winner(board)
    if w == 1:
        return 10 - depth      # prefer faster wins
    if w == -1:
        return depth - 10      # prefer slower losses
    if not any(0 in row for row in board):
        return 0               # draw
    return None


def _minimax(board: List[List[int]], turn: int, depth: int, alpha: int, beta: int) -> int:
    tv = _terminal_value(board, depth)
    if tv is not None:
        return tv

    moves = _empty_cells(board)

    if turn == 1:
        best = -10**9
        for r, c in moves:
            board[r][c] = 1
            val = _minimax(board, -1, depth + 1, alpha, beta)
            board[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for r, c in moves:
            board[r][c] = -1
            val = _minimax(board, 1, depth + 1, alpha, beta)
            board[r][c] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    moves = _empty_cells(board)
    if not moves:
        return (0, 0)  # fallback; arena should normally avoid terminal/full boards

    best_move = moves[0]
    best_score = -10**9

    for r, c in moves:
        board[r][c] = 1
        score = _minimax(board, -1, 1, -10**9, 10**9)
        board[r][c] = 0

        # Primary: better minimax score
        # Secondary: better positional priority
        if (
            score > best_score
            or (score == best_score and MOVE_PRIORITY[(r, c)] > MOVE_PRIORITY[best_move])
        ):
            best_score = score
            best_move = (r, c)

    return best_move
