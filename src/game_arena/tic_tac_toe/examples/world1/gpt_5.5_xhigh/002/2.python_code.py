
from functools import lru_cache

_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Preferred order for stable tie-breaking: center, corners, then edges.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
_ORDER_RANK = {move: rank for rank, move in enumerate(_MOVE_ORDER)}
_INF = 10**9


def _to_cells(board):
    cells = []
    for r in range(3):
        for c in range(3):
            v = int(board[r][c])
            if v > 0:
                cells.append(1)
            elif v < 0:
                cells.append(-1)
            else:
                cells.append(0)
    return tuple(cells)


def _place(cells, idx, mark):
    return cells[:idx] + (mark,) + cells[idx + 1:]


@lru_cache(maxsize=None)
def _legal_indices(cells):
    return tuple(i for i in _MOVE_ORDER if cells[i] == 0)


@lru_cache(maxsize=None)
def _winner(cells):
    for a, b, c in _WIN_LINES:
        s = cells[a] + cells[b] + cells[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _minimax(cells, turn):
    """
    Exact game-theoretic value from our perspective.
    Positive is good for us, negative is good for the opponent.
    Faster wins and slower losses are preferred.
    """
    legal = _legal_indices(cells)
    empty_count = len(legal)
    win = _winner(cells)

    if win == 1:
        return 10 + empty_count
    if win == -1:
        return -10 - empty_count
    if empty_count == 0:
        return 0

    if turn == 1:
        best = -_INF
        for idx in legal:
            best = max(best, _minimax(_place(cells, idx, 1), -1))
        return best
    else:
        best = _INF
        for idx in legal:
            best = min(best, _minimax(_place(cells, idx, -1), 1))
        return best


@lru_cache(maxsize=None)
def _practical_value(cells, turn):
    """
    Secondary tie-breaker: estimate value against a fallible/random opponent,
    while our own moves still preserve the minimax-optimal outcome.
    """
    legal = _legal_indices(cells)
    empty_count = len(legal)
    win = _winner(cells)

    if win == 1:
        return 1.0 + 0.01 * empty_count
    if win == -1:
        return -1.0 - 0.01 * empty_count
    if empty_count == 0:
        return 0.0

    if turn == 1:
        best_mm = -_INF
        best_practical = -float("inf")

        for idx in legal:
            child = _place(cells, idx, 1)
            mm = _minimax(child, -1)

            if mm > best_mm:
                best_mm = mm
                best_practical = _practical_value(child, -1)
            elif mm == best_mm:
                best_practical = max(best_practical, _practical_value(child, -1))

        return best_practical

    # Opponent model for the tie-breaker: random legal play.
    total = 0.0
    for idx in legal:
        total += _practical_value(_place(cells, idx, -1), 1)
    return total / empty_count


def policy(board: list[list[int]]) -> tuple[int, int]:
    cells = _to_cells(board)
    legal = _legal_indices(cells)

    # If the board is full, no legal move exists. This should not be called then,
    # but return a valid-shaped tuple as a final safeguard.
    if not legal:
        return (0, 0)

    # If game is already over but empty cells remain, still return a legal cell.
    if len(legal) == 1 or _winner(cells) != 0:
        return divmod(legal[0], 3)

    # First choose only moves with the best exact minimax value.
    best_score = -_INF
    candidates = []

    for idx in legal:
        child = _place(cells, idx, 1)
        score = _minimax(child, -1)

        if score > best_score:
            best_score = score
            candidates = [(idx, child)]
        elif score == best_score:
            candidates.append((idx, child))

    # Among equally perfect moves, prefer lines that punish opponent mistakes.
    best_idx = candidates[0][0]
    best_key = None

    for idx, child in candidates:
        key = (_practical_value(child, -1), -_ORDER_RANK[idx])
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return divmod(best_idx, 3)
