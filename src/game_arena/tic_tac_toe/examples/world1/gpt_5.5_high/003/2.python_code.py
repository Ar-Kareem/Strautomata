
from functools import lru_cache

_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Center, corners, then edges.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _to_cells(board):
    cells = []
    for r in range(3):
        for c in range(3):
            v = board[r][c]
            if v == 1:
                cells.append(1)
            elif v == -1:
                cells.append(-1)
            else:
                cells.append(0)
    return tuple(cells)


@lru_cache(maxsize=None)
def _winner(cells):
    for a, b, c in _WIN_LINES:
        if cells[a] != 0 and cells[a] == cells[b] == cells[c]:
            return cells[a]
    return 0


def _first_empty(cells):
    for idx in _MOVE_ORDER:
        if cells[idx] == 0:
            return divmod(idx, 3)
    return (0, 0)


def _winning_moves(cells, player):
    moves = []
    for idx in _MOVE_ORDER:
        if cells[idx] == 0:
            child = list(cells)
            child[idx] = player
            if _winner(tuple(child)) == player:
                moves.append(idx)
    return moves


@lru_cache(maxsize=None)
def _minimax(cells, turn):
    """
    Returns value from our perspective:
    positive = good for player 1, negative = good for player -1.
    """
    w = _winner(cells)
    empty_count = cells.count(0)

    if w == 1:
        return 100 + empty_count  # Faster wins are better.
    if w == -1:
        return -100 - empty_count  # Slower losses are less bad.
    if empty_count == 0:
        return 0

    if turn == 1:
        best = -10_000
        for idx in _MOVE_ORDER:
            if cells[idx] == 0:
                child = list(cells)
                child[idx] = 1
                best = max(best, _minimax(tuple(child), -1))
        return best

    best = 10_000
    for idx in _MOVE_ORDER:
        if cells[idx] == 0:
            child = list(cells)
            child[idx] = -1
            best = min(best, _minimax(tuple(child), 1))
    return best


def _tie_break_score(cells):
    """
    Used only among moves with identical minimax value.
    Favors center control, corners, threats, and forks.
    """
    score = 0

    if cells[4] == 1:
        score += 6
    elif cells[4] == -1:
        score -= 6

    for idx in (0, 2, 6, 8):
        if cells[idx] == 1:
            score += 2
        elif cells[idx] == -1:
            score -= 2

    for idx in (1, 3, 5, 7):
        if cells[idx] == 1:
            score += 1
        elif cells[idx] == -1:
            score -= 1

    own_threats = 0
    opp_threats = 0

    for a, b, c in _WIN_LINES:
        line = (cells[a], cells[b], cells[c])
        own = line.count(1)
        opp = line.count(-1)
        empty = line.count(0)

        if opp == 0:
            if own == 2 and empty == 1:
                own_threats += 1
                score += 40
            elif own == 1 and empty == 2:
                score += 4

        if own == 0:
            if opp == 2 and empty == 1:
                opp_threats += 1
                score -= 45
            elif opp == 1 and empty == 2:
                score -= 3

    if own_threats >= 2:
        score += 80
    if opp_threats >= 2:
        score -= 80

    return score


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        cells = _to_cells(board)
    except Exception:
        return (1, 1)

    if cells.count(0) == 0:
        return (0, 0)

    # If called on an already-terminal board, still return a legal empty cell.
    if _winner(cells) != 0:
        return _first_empty(cells)

    # Strong opening book.
    if cells.count(0) == 9:
        return (1, 1)

    # If opponent opened and we are responding for the first time.
    if cells.count(1) == 0 and cells.count(-1) == 1:
        if cells[4] == 0:
            return (1, 1)
        for idx in (0, 2, 6, 8):
            if cells[idx] == 0:
                return divmod(idx, 3)
        return _first_empty(cells)

    # Win immediately if possible.
    wins = _winning_moves(cells, 1)
    if wins:
        return divmod(wins[0], 3)

    # Block a single immediate opponent win.
    blocks = _winning_moves(cells, -1)
    if len(blocks) == 1:
        return divmod(blocks[0], 3)

    # Otherwise choose the optimal minimax move.
    best_idx = None
    best_value = -10_000
    best_tie = -10_000

    for idx in _MOVE_ORDER:
        if cells[idx] != 0:
            continue

        child = list(cells)
        child[idx] = 1
        child = tuple(child)

        value = _minimax(child, -1)
        tie = _tie_break_score(child)

        if value > best_value or (value == best_value and tie > best_tie):
            best_value = value
            best_tie = tie
            best_idx = idx

    if best_idx is None:
        return _first_empty(cells)

    return divmod(best_idx, 3)
