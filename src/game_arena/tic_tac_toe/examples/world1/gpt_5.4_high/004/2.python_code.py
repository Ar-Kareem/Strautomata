
from functools import lru_cache

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

# Prefer center, then corners, then edges.
MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
POS_WEIGHT = (3, 2, 3, 2, 4, 2, 3, 2, 3)


def _winner(state: tuple[int, ...]) -> int:
    for a, b, c in WIN_LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _legal_moves(state: tuple[int, ...]) -> list[int]:
    return [i for i in MOVE_ORDER if state[i] == 0]


def _line_potential(state: tuple[int, ...]) -> int:
    score = 0
    for a, b, c in WIN_LINES:
        vals = (state[a], state[b], state[c])
        c1 = vals.count(1)
        c_1 = vals.count(-1)
        c0 = 3 - c1 - c_1

        # Lines open for us.
        if c_1 == 0:
            if c1 == 2 and c0 == 1:
                score += 6
            elif c1 == 1 and c0 == 2:
                score += 2

        # Lines open for the opponent.
        if c1 == 0:
            if c_1 == 2 and c0 == 1:
                score -= 6
            elif c_1 == 1 and c0 == 2:
                score -= 2

    return score


def _count_immediate_wins(state: tuple[int, ...], player: int) -> int:
    total = 0
    for i in MOVE_ORDER:
        if state[i] != 0:
            continue
        nxt = list(state)
        nxt[i] = player
        if _winner(tuple(nxt)) == player:
            total += 1
    return total


def _tiebreak(state: tuple[int, ...], move: int) -> int:
    return (
        100 * POS_WEIGHT[move]
        + 40 * _count_immediate_wins(state, 1)
        - 50 * _count_immediate_wins(state, -1)
        + _line_potential(state)
    )


@lru_cache(maxsize=None)
def _solve(state: tuple[int, ...], player: int) -> int:
    """
    Exact minimax value from our perspective:
    positive = good for us (player 1),
    negative = good for opponent (player -1).
    """
    w = _winner(state)
    if w != 0:
        # Prefer faster wins and slower losses.
        return w * (10 + state.count(0))

    if 0 not in state:
        return 0

    moves = _legal_moves(state)

    if player == 1:
        best = -10**9
        for i in moves:
            nxt = list(state)
            nxt[i] = 1
            best = max(best, _solve(tuple(nxt), -1))
        return best
    else:
        best = 10**9
        for i in moves:
            nxt = list(state)
            nxt[i] = -1
            best = min(best, _solve(tuple(nxt), 1))
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    moves = _legal_moves(state)

    # Fallback for a full board; should not normally happen.
    if not moves:
        return (0, 0)

    # If the position is already terminal but still has empty cells,
    # just return any legal move.
    if _winner(state) != 0:
        i = moves[0]
        return (i // 3, i % 3)

    best_move = moves[0]
    best_value = -10**9
    best_tiebreak = -10**9

    for i in moves:
        nxt = list(state)
        nxt[i] = 1
        nxt_state = tuple(nxt)

        value = _solve(nxt_state, -1)
        tb = _tiebreak(nxt_state, i)

        if value > best_value or (value == best_value and tb > best_tiebreak):
            best_value = value
            best_tiebreak = tb
            best_move = i

    # Extra safety: ensure returned move is legal.
    if state[best_move] != 0:
        for i in range(9):
            if state[i] == 0:
                return (i // 3, i % 3)
        return (0, 0)

    return (best_move // 3, best_move % 3)
