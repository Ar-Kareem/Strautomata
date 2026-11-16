
from typing import List, Tuple

WIN_LINES = (
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
)

MOVE_ORDER = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _winner(board: List[List[int]]) -> int:
    """Return 1 if we won, -1 if opponent won, 0 otherwise."""
    for line in WIN_LINES:
        s = board[line[0][0]][line[0][1]] + board[line[1][0]][line[1][1]] + board[line[2][0]][line[2][1]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _has_empty(board: List[List[int]]) -> bool:
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return True
    return False


def _legal_moves_ordered(board: List[List[int]]):
    for r, c in MOVE_ORDER:
        if board[r][c] == 0:
            yield (r, c)


def _immediate_winning_move(board: List[List[int]], player: int):
    """Return a winning move for player if one exists, else None."""
    for r, c in _legal_moves_ordered(board):
        board[r][c] = player
        if _winner(board) == player:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    return None


def _minimax(board: List[List[int]], player: int, depth: int, alpha: int, beta: int) -> int:
    """
    Score from our perspective.
    Positive is good for player 1, negative is good for player -1.
    Depth is used to prefer quicker wins and delayed losses.
    """
    w = _winner(board)
    if w == 1:
        return 10 - depth
    if w == -1:
        return depth - 10
    if not _has_empty(board):
        return 0

    if player == 1:
        best = -100
        for r, c in _legal_moves_ordered(board):
            board[r][c] = 1
            score = _minimax(board, -1, depth + 1, alpha, beta)
            board[r][c] = 0
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        best = 100
        for r, c in _legal_moves_ordered(board):
            board[r][c] = -1
            score = _minimax(board, 1, depth + 1, alpha, beta)
            board[r][c] = 0
            if score < best:
                best = score
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move as (row, col), always choosing a legal empty cell.
    Board values: 0 empty, 1 our move, -1 opponent move.
    """
    # Gather legal moves first, ensuring we can always return one.
    legal = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not legal:
        # No legal move exists in a terminal/full board. This should not be called then,
        # but return a valid-shaped tuple as a final safeguard.
        return (0, 0)

    # If we can win immediately, do it.
    move = _immediate_winning_move(board, 1)
    if move is not None:
        return move

    # If opponent can win immediately, block it.
    move = _immediate_winning_move(board, -1)
    if move is not None:
        return move

    # Otherwise use perfect minimax play.
    best_score = -100
    best_move = legal[0]

    for r, c in _legal_moves_ordered(board):
        board[r][c] = 1
        score = _minimax(board, -1, 1, -100, 100)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Final legality safeguard.
    if board[best_move[0]][best_move[1]] == 0:
        return best_move
    return legal[0]
