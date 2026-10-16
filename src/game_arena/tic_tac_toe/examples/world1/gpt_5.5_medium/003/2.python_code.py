
from functools import lru_cache

WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

CENTER = 4
CORNERS = (0, 2, 6, 8)


def _winner(cells):
    for a, b, c in WIN_LINES:
        s = cells[a] + cells[b] + cells[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_indices(cells):
    return [i for i, v in enumerate(cells) if v == 0]


def _immediate_winning_moves(cells, player):
    moves = []
    for i, v in enumerate(cells):
        if v == 0:
            new_cells = list(cells)
            new_cells[i] = player
            if _winner(tuple(new_cells)) == player:
                moves.append(i)
    return moves


@lru_cache(maxsize=None)
def _minimax(cells, turn):
    """
    Returns a score from our perspective.
    Positive is good for player 1, negative is good for player -1.
    The magnitude slightly prefers faster wins and slower losses.
    """
    w = _winner(cells)
    filled = 9 - cells.count(0)

    if w == 1:
        return 100 - filled
    if w == -1:
        return -100 + filled

    empties = _empty_indices(cells)
    if not empties:
        return 0

    if turn == 1:
        best = -10_000
        for i in empties:
            new_cells = list(cells)
            new_cells[i] = 1
            best = max(best, _minimax(tuple(new_cells), -1))
        return best
    else:
        best = 10_000
        for i in empties:
            new_cells = list(cells)
            new_cells[i] = -1
            best = min(best, _minimax(tuple(new_cells), 1))
        return best


def _positional_tiebreak(cells):
    """
    Heuristic used only to choose among equally optimal minimax moves.
    It favors positions that create pressure and give weaker opponents
    more chances to make a losing mistake.
    """
    score = 0

    # Center and corners are generally strongest.
    if cells[CENTER] == 1:
        score += 8
    elif cells[CENTER] == -1:
        score -= 8

    for i in CORNERS:
        if cells[i] == 1:
            score += 4
        elif cells[i] == -1:
            score -= 4

    # Reward open lines and two-in-a-row threats.
    for line in WIN_LINES:
        vals = [cells[i] for i in line]
        mine = vals.count(1)
        opp = vals.count(-1)
        empty = vals.count(0)

        if opp == 0:
            if mine == 1 and empty == 2:
                score += 3
            elif mine == 2 and empty == 1:
                score += 18

        if mine == 0:
            if opp == 1 and empty == 2:
                score -= 2
            elif opp == 2 and empty == 1:
                score -= 22

    my_wins = len(_immediate_winning_moves(cells, 1))
    opp_wins = len(_immediate_winning_moves(cells, -1))

    # Forks: multiple immediate threats are very powerful.
    score += 30 * my_wins
    score -= 35 * opp_wins

    if my_wins >= 2:
        score += 50
    if opp_wins >= 2:
        score -= 60

    return score


def _move_priority(index):
    if index == CENTER:
        return 3
    if index in CORNERS:
        return 2
    return 1


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move as (row, col) for player 1.
    The input board uses:
      0  = empty
      1  = our mark
      -1 = opponent mark
    """
    cells = []
    for r in range(3):
        for c in range(3):
            try:
                v = int(board[r][c])
            except Exception:
                v = 0
            if v not in (-1, 0, 1):
                v = 0
            cells.append(v)

    cells = tuple(cells)
    legal = _empty_indices(cells)

    # The game engine should not call us on a full board, but keep a safe fallback.
    if not legal:
        return (0, 0)

    # If we can win immediately, do it.
    winning = _immediate_winning_moves(cells, 1)
    if winning:
        i = max(winning, key=lambda x: _move_priority(x))
        return (i // 3, i % 3)

    best_i = legal[0]
    best_key = (-10_000, -10_000, -10_000)

    for i in legal:
        new_cells = list(cells)
        new_cells[i] = 1
        new_cells = tuple(new_cells)

        minimax_score = _minimax(new_cells, -1)
        tie_score = _positional_tiebreak(new_cells)
        priority = _move_priority(i)

        key = (minimax_score, tie_score, priority)

        if key > best_key:
            best_key = key
            best_i = i

    return (best_i // 3, best_i % 3)
