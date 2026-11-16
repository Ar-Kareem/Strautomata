
from functools import lru_cache

# Preferred move order: center, corners, then edges.
MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)

# Winning line indices on a flattened 3x3 board.
WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _winner(cells: tuple[int, ...]) -> int:
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for a, b, c in WIN_LINES:
        s = cells[a] + cells[b] + cells[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _solve(cells: tuple[int, ...], player: int) -> int:
    """
    Minimax value from our perspective.
    Returns:
        1  -> forced win for us
        0  -> forced draw
       -1  -> forced loss for us
    'player' is whose turn it is: 1 for us, -1 for opponent.
    """
    w = _winner(cells)
    if w != 0:
        return w
    if 0 not in cells:
        return 0

    if player == 1:
        best = -2
        for i in MOVE_ORDER:
            if cells[i] == 0:
                nxt = list(cells)
                nxt[i] = 1
                score = _solve(tuple(nxt), -1)
                if score > best:
                    best = score
                    if best == 1:
                        break
        return best
    else:
        best = 2
        for i in MOVE_ORDER:
            if cells[i] == 0:
                nxt = list(cells)
                nxt[i] = -1
                score = _solve(tuple(nxt), 1)
                if score < best:
                    best = score
                    if best == -1:
                        break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Choose a legal move (row, col) for the current board.
    0 = empty, 1 = our marks, -1 = opponent marks.
    """
    cells = tuple(int(board[r][c]) for r in range(3) for c in range(3))
    empties = [i for i in MOVE_ORDER if cells[i] == 0]

    # Normal play should never call policy on a full board,
    # but keep a safe fallback.
    if not empties:
        return (0, 0)

    # 1) Take an immediate win if available.
    for i in empties:
        nxt = list(cells)
        nxt[i] = 1
        if _winner(tuple(nxt)) == 1:
            return divmod(i, 3)

    # 2) Block an immediate opponent win if necessary.
    for i in empties:
        nxt = list(cells)
        nxt[i] = -1
        if _winner(tuple(nxt)) == -1:
            return divmod(i, 3)

    # 3) Otherwise use perfect-play minimax.
    best_score = -2
    best_move = empties[0]

    for i in empties:
        nxt = list(cells)
        nxt[i] = 1
        score = _solve(tuple(nxt), -1)
        if score > best_score:
            best_score = score
            best_move = i
            if best_score == 1:
                break

    return divmod(best_move, 3)
