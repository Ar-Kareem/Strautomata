
from typing import List, Tuple

Move = Tuple[int, int]

# Preferred move ordering for tie-breaking:
# center, corners, edges
PREFERRED_MOVES = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]


def _winner(board: List[List[int]]) -> int:
    # Rows
    for r in range(3):
        s = board[r][0] + board[r][1] + board[r][2]
        if s == 3:
            return 1
        if s == -3:
            return -1

    # Columns
    for c in range(3):
        s = board[0][c] + board[1][c] + board[2][c]
        if s == 3:
            return 1
        if s == -3:
            return -1

    # Diagonals
    s = board[0][0] + board[1][1] + board[2][2]
    if s == 3:
        return 1
    if s == -3:
        return -1

    s = board[0][2] + board[1][1] + board[2][0]
    if s == 3:
        return 1
    if s == -3:
        return -1

    return 0


def _is_full(board: List[List[int]]) -> bool:
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return False
    return True


def _legal_moves(board: List[List[int]]) -> List[Move]:
    return [(r, c) for (r, c) in PREFERRED_MOVES if board[r][c] == 0]


def _board_key(board: List[List[int]], player: int):
    return tuple(tuple(row) for row in board), player


_MEMO = {}


def _minimax(board: List[List[int]], player: int) -> int:
    """
    Returns the game-theoretic value from the perspective of player 1 (us):
    +1 = forced win for us
     0 = forced draw
    -1 = forced loss for us
    """
    w = _winner(board)
    if w != 0:
        return w
    if _is_full(board):
        return 0

    key = _board_key(board, player)
    if key in _MEMO:
        return _MEMO[key]

    moves = _legal_moves(board)

    if player == 1:
        best = -2
        for r, c in moves:
            board[r][c] = 1
            val = _minimax(board, -1)
            board[r][c] = 0
            if val > best:
                best = val
            if best == 1:
                break
    else:
        best = 2
        for r, c in moves:
            board[r][c] = -1
            val = _minimax(board, 1)
            board[r][c] = 0
            if val < best:
                best = val
            if best == -1:
                break

    _MEMO[key] = best
    return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    moves = _legal_moves(board)

    # Safety fallback: if somehow called on a full board, return an in-bounds move.
    # Arena states are expected to have at least one legal move.
    if not moves:
        return (0, 0)

    # 1) Immediate win
    for r, c in moves:
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2) Immediate block
    for r, c in moves:
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3) Full minimax
    best_move = moves[0]
    best_val = -2

    for r, c in moves:
        board[r][c] = 1
        val = _minimax(board, -1)
        board[r][c] = 0

        if val > best_val:
            best_val = val
            best_move = (r, c)

    return best_move
