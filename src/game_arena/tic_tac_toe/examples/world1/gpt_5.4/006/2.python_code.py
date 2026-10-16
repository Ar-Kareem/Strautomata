
from typing import List, Tuple

Move = Tuple[int, int]

# Preferred move order for tie-breaking among equally optimal moves.
# Center > corners > edges
PREFERRED_ORDER = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]


def _legal_moves(board: List[List[int]]) -> List[Move]:
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]


def _winner(board: List[List[int]]) -> int:
    lines = []

    # Rows and columns
    for i in range(3):
        lines.append(board[i])
        lines.append([board[0][i], board[1][i], board[2][i]])

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


def _is_full(board: List[List[int]]) -> bool:
    return all(board[r][c] != 0 for r in range(3) for c in range(3))


def _ordered_moves(board: List[List[int]]) -> List[Move]:
    legal = set(_legal_moves(board))
    return [mv for mv in PREFERRED_ORDER if mv in legal]


def _minimax(board: List[List[int]], player: int, alpha: int, beta: int) -> int:
    w = _winner(board)
    if w != 0:
        return w
    if _is_full(board):
        return 0

    moves = _ordered_moves(board)

    if player == 1:
        best = -2
        for r, c in moves:
            board[r][c] = 1
            score = _minimax(board, -1, alpha, beta)
            board[r][c] = 0
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 2
        for r, c in moves:
            board[r][c] = -1
            score = _minimax(board, 1, alpha, beta)
            board[r][c] = 0
            if score < best:
                best = score
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    moves = _ordered_moves(board)
    if not moves:
        # No legal move exists; return a valid in-bounds coordinate fallback.
        # In normal arena play this should never be used.
        return (0, 0)

    # Immediate win
    for r, c in moves:
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block
    for r, c in moves:
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Full minimax search
    best_score = -2
    best_move = moves[0]

    for r, c in moves:
        board[r][c] = 1
        score = _minimax(board, -1, -2, 2)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
