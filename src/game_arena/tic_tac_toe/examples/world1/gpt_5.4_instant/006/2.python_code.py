
from functools import lru_cache

# Preferred move order for deterministic tie-breaking:
# center, corners, then edges
PREFERRED_MOVES = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]

WIN_LINES = [
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
]

def _board_to_tuple(board):
    return tuple(tuple(row) for row in board)

def _empty_cells(board):
    cells = []
    for r, c in PREFERRED_MOVES:
        if board[r][c] == 0:
            cells.append((r, c))
    return cells

def _winner(board):
    for line in WIN_LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _is_full(board):
    for row in board:
        for v in row:
            if v == 0:
                return False
    return True

@lru_cache(maxsize=None)
def _solve(board_t, player):
    # player is whose turn it is on this board: 1 or -1
    board = [list(row) for row in board_t]

    w = _winner(board)
    if w != 0:
        return w, None
    if _is_full(board):
        return 0, None

    best_score = -2
    best_move = None

    for r, c in _empty_cells(board):
        board[r][c] = player
        next_t = _board_to_tuple(board)
        child_score, _ = _solve(next_t, -player)
        board[r][c] = 0

        # child_score is from next player's perspective outcome:
        # +1 means next player wins, -1 means next player loses.
        # So from current player's perspective:
        score = -child_score

        if score > best_score:
            best_score = score
            best_move = (r, c)
            if best_score == 1:
                break

    return best_score, best_move

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect legal moves safely
    legal = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

    # Must always return a legal move string/tuple; if malformed input somehow
    # leaves no legal moves, return a valid in-bounds fallback.
    if not legal:
        return (0, 0)

    # Fast path: immediate winning move
    for r, c in _empty_cells(board):
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Fast path: block opponent's immediate winning move
    for r, c in _empty_cells(board):
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Full optimal search
    board_t = _board_to_tuple(board)
    _, move = _solve(board_t, 1)

    if move is not None and board[move[0]][move[1]] == 0:
        return move

    # Safety fallback: choose preferred legal move
    for mv in PREFERRED_MOVES:
        if mv in legal:
            return mv

    return legal[0]
