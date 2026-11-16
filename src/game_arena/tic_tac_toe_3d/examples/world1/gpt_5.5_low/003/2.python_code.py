
import time
from functools import lru_cache

# ---------- Precomputed geometry ----------

CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

def _make_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append(tuple((i, j, k) for i in range(3)))
    for i in range(3):
        for k in range(3):
            lines.append(tuple((i, j, k) for j in range(3)))
    for i in range(3):
        for j in range(3):
            lines.append(tuple((i, j, k) for k in range(3)))

    # Plane diagonals: fixed i
    for i in range(3):
        lines.append(tuple((i, t, t) for t in range(3)))
        lines.append(tuple((i, t, 2 - t) for t in range(3)))

    # Plane diagonals: fixed j
    for j in range(3):
        lines.append(tuple((t, j, t) for t in range(3)))
        lines.append(tuple((t, j, 2 - t) for t in range(3)))

    # Plane diagonals: fixed k
    for k in range(3):
        lines.append(tuple((t, t, k) for t in range(3)))
        lines.append(tuple((t, 2 - t, k) for t in range(3)))

    # Space diagonals
    lines.append(tuple((t, t, t) for t in range(3)))
    lines.append(tuple((t, t, 2 - t) for t in range(3)))
    lines.append(tuple((t, 2 - t, t) for t in range(3)))
    lines.append(tuple((t, 2 - t, 2 - t) for t in range(3)))

    # Remove accidental duplicates, preserving order
    seen = set()
    unique = []
    for line in lines:
        s = frozenset(line)
        if s not in seen:
            seen.add(s)
            unique.append(line)
    return tuple(unique)

LINES = _make_lines()

CELL_LINES = {c: 0 for c in CELLS}
for line in LINES:
    for c in line:
        CELL_LINES[c] += 1

# Positional preference: number of winning lines through the cell is very important.
# The center is strongest in 3x3x3.
POSITION_SCORE = {}
for c in CELLS:
    i, j, k = c
    dist_from_center = abs(i - 1) + abs(j - 1) + abs(k - 1)
    POSITION_SCORE[c] = CELL_LINES[c] * 10 - dist_from_center

ORDERED_CELLS = sorted(CELLS, key=lambda c: POSITION_SCORE[c], reverse=True)


# ---------- Helpers ----------

def _get(board, c):
    i, j, k = c
    return board[i][j][k]

def _set(board, c, v):
    i, j, k = c
    board[i][j][k] = v

def _legal_moves(board):
    return [c for c in ORDERED_CELLS if _get(board, c) == 0]

def _has_win(board, player):
    for line in LINES:
        if all(_get(board, c) == player for c in line):
            return True
    return False

def _winning_move(board, player):
    for line in LINES:
        vals = [_get(board, c) for c in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            return line[vals.index(0)]
    return None

def _board_key(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


# ---------- Evaluation ----------

def _evaluate(board):
    if _has_win(board, 1):
        return 1_000_000
    if _has_win(board, -1):
        return -1_000_000

    score = 0
    my_twos = 0
    opp_twos = 0

    # Line-based evaluation
    for line in LINES:
        s = sum(_get(board, c) for c in line)

        # Only our marks and empties
        if all(_get(board, c) >= 0 for c in line):
            if s == 2:
                score += 120
                my_twos += 1
            elif s == 1:
                score += 8

        # Only opponent marks and empties
        if all(_get(board, c) <= 0 for c in line):
            if s == -2:
                score -= 150
                opp_twos += 1
            elif s == -1:
                score -= 9

    # Fork pressure: multiple two-in-a-row threats are very valuable/dangerous.
    if my_twos >= 2:
        score += 80 * my_twos * my_twos
    if opp_twos >= 2:
        score -= 100 * opp_twos * opp_twos

    # Positional value
    for c in CELLS:
        v = _get(board, c)
        if v == 1:
            score += POSITION_SCORE[c]
        elif v == -1:
            score -= POSITION_SCORE[c]

    return score


# ---------- Minimax with alpha-beta ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = time.perf_counter()
    time_limit = 0.92

    legal = _legal_moves(board)
    if not legal:
        return (0, 0, 0)

    # 1. Win immediately if possible.
    move = _winning_move(board, 1)
    if move is not None and _get(board, move) == 0:
        return move

    # 2. Block opponent's immediate win.
    move = _winning_move(board, -1)
    if move is not None and _get(board, move) == 0:
        return move

    empties = len(legal)

    # Adaptive depth. Early game has huge branching; late game can search deeper.
    if empties >= 22:
        depth = 3
    elif empties >= 16:
        depth = 4
    elif empties >= 11:
        depth = 5
    elif empties >= 8:
        depth = 7
    else:
        depth = empties

    # If board is empty, center is optimal.
    if empties == 27:
        return (1, 1, 1)

    cache = {}

    def ordered_moves():
        # Tactical ordering: winning/blocking-related cells and positional strength first.
        moves = _legal_moves(board)
        scored = []
        for c in moves:
            sc = POSITION_SCORE[c]

            _set(board, c, 1)
            if _has_win(board, 1):
                sc += 100000
            _set(board, c, 0)

            _set(board, c, -1)
            if _has_win(board, -1):
                sc += 90000
            _set(board, c, 0)

            # Favor moves participating in currently open lines.
            for line in LINES:
                if c in line:
                    vals = [_get(board, x) for x in line]
                    if -1 not in vals:
                        sc += vals.count(1) * 12
                    if 1 not in vals:
                        sc += vals.count(-1) * 14
            scored.append((sc, c))

        scored.sort(reverse=True)
        return [c for _, c in scored]

    def alphabeta(d, alpha, beta, player):
        if time.perf_counter() - start > time_limit:
            raise TimeoutError

        key = (_board_key(board), d, player)
        if key in cache:
            return cache[key]

        if _has_win(board, 1):
            return 1_000_000 + d
        if _has_win(board, -1):
            return -1_000_000 - d

        moves = _legal_moves(board)
        if d == 0 or not moves:
            return _evaluate(board)

        if player == 1:
            value = -10**9
            for c in ordered_moves():
                _set(board, c, 1)
                value = max(value, alphabeta(d - 1, alpha, beta, -1))
                _set(board, c, 0)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = 10**9
            for c in ordered_moves():
                _set(board, c, -1)
                value = min(value, alphabeta(d - 1, alpha, beta, 1))
                _set(board, c, 0)
                beta = min(beta, value)
                if alpha >= beta:
                    break

        cache[key] = value
        return value

    # 3. Search for the best move.
    best_move = legal[0]
    best_value = -10**9

    try:
        for c in ordered_moves():
            if _get(board, c) != 0:
                continue

            _set(board, c, 1)
            val = alphabeta(depth - 1, -10**9, 10**9, -1)
            _set(board, c, 0)

            # Small tie-breaker for positional strength.
            val += POSITION_SCORE[c] * 0.01

            if val > best_value:
                best_value = val
                best_move = c

    except TimeoutError:
        # Return the best move found so far.
        if _get(board, best_move) == 0:
            return best_move

    # 4. Final legality guarantee.
    if _get(board, best_move) == 0:
        return best_move

    for c in ORDERED_CELLS:
        if _get(board, c) == 0:
            return c

    return legal[0]
