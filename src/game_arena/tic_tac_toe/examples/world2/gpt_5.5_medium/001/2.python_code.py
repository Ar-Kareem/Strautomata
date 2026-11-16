
"""
4x4 Tic Tac Toe policy.

Assumptions:
- Board is 4x4.
- 0 = empty, 1 = this policy, -1 = opponent.
- A win is four in a row: any full row, column, or main diagonal.
"""

from time import perf_counter

# Winning lines on a 4x4 board: 4 rows, 4 columns, 2 diagonals.
_LINES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (8, 9, 10, 11),
    (12, 13, 14, 15),
    (0, 4, 8, 12),
    (1, 5, 9, 13),
    (2, 6, 10, 14),
    (3, 7, 11, 15),
    (0, 5, 10, 15),
    (3, 6, 9, 12),
)

_LINES_THROUGH = [[] for _ in range(16)]
for line in _LINES:
    for cell in line:
        _LINES_THROUGH[cell].append(line)
_LINES_THROUGH = tuple(tuple(x) for x in _LINES_THROUGH)

# Static preference: cells in more winning lines and nearer the center are preferred.
_BASE = []
for i in range(16):
    r, c = divmod(i, 4)
    center_bonus = 4 - abs(2 * r - 3) - abs(2 * c - 3)
    _BASE.append(10 * len(_LINES_THROUGH[i]) + center_bonus)
_BASE = tuple(_BASE)

_INF = 10**9
_WIN = 10**7
_TIME_LIMIT = 0.88

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0 and perf_counter() > _DEADLINE:
        raise _Timeout()


def _winner(flat):
    for line in _LINES:
        s = flat[line[0]] + flat[line[1]] + flat[line[2]] + flat[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _would_win(flat, idx, side):
    """True if placing side at idx immediately completes a winning line."""
    if flat[idx] != 0:
        return False
    for line in _LINES_THROUGH[idx]:
        ok = True
        for j in line:
            if j != idx and flat[j] != side:
                ok = False
                break
        if ok:
            return True
    return False


def _immediate_winning_moves(flat, side):
    return [i for i, v in enumerate(flat) if v == 0 and _would_win(flat, i, side)]


def _count_immediate_after(flat, side):
    cnt = 0
    for i, v in enumerate(flat):
        if v == 0 and _would_win(flat, i, side):
            cnt += 1
    return cnt


def _evaluate(flat):
    """Heuristic score from player 1's perspective."""
    w = _winner(flat)
    if w == 1:
        return _WIN
    if w == -1:
        return -_WIN

    score = 0
    weights = (0, 3, 45, 6000, _WIN)

    for line in _LINES:
        p = 0
        o = 0
        for i in line:
            if flat[i] == 1:
                p += 1
            elif flat[i] == -1:
                o += 1

        if p and o:
            continue
        if p:
            score += weights[p]
        elif o:
            score -= weights[o]

    # Immediate threat/fork awareness.
    my_threats = _count_immediate_after(flat, 1)
    op_threats = _count_immediate_after(flat, -1)

    if my_threats:
        score += 9000 * my_threats
        if my_threats >= 2:
            score += 120000
    if op_threats:
        score -= 9000 * op_threats
        if op_threats >= 2:
            score -= 120000

    return score


def _move_score(flat, idx, side):
    """Ordering score for alpha-beta. Larger means search earlier."""
    opp = -side
    score = _BASE[idx]

    if _would_win(flat, idx, side):
        score += 1_000_000
    if _would_win(flat, idx, opp):
        score += 850_000

    # Prefer moves that create multiple immediate threats.
    flat[idx] = side
    threats = _count_immediate_after(flat, side)
    score += 55_000 * threats

    # Local line potential.
    for line in _LINES_THROUGH[idx]:
        mine = 0
        theirs = 0
        for j in line:
            if flat[j] == side:
                mine += 1
            elif flat[j] == opp:
                theirs += 1

        if theirs == 0:
            if mine == 2:
                score += 80
            elif mine == 3:
                score += 5000

    flat[idx] = 0

    # Blocking opponent's developing lines.
    for line in _LINES_THROUGH[idx]:
        mine = 0
        theirs = 0
        for j in line:
            if j == idx:
                continue
            if flat[j] == side:
                mine += 1
            elif flat[j] == opp:
                theirs += 1

        if mine == 0:
            if theirs == 2:
                score += 70
            elif theirs == 3:
                score += 6000

    return score


def _ordered_moves(flat, side):
    moves = [i for i, v in enumerate(flat) if v == 0]
    moves.sort(key=lambda m: _move_score(flat, m, side), reverse=True)
    return moves


def _alphabeta(flat, side, depth, alpha, beta):
    _check_time()

    w = _winner(flat)
    empty_count = flat.count(0)

    if w == 1:
        return _WIN + empty_count
    if w == -1:
        return -_WIN - empty_count
    if empty_count == 0:
        return 0
    if depth <= 0:
        return _evaluate(flat)

    key = (tuple(flat), side)
    entry = _TT.get(key)
    if entry is not None:
        stored_depth, flag, val = entry
        if stored_depth >= depth:
            if flag == 0:      # exact
                return val
            elif flag == 1:    # lower bound
                if val > alpha:
                    alpha = val
            else:              # upper bound
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    orig_alpha = alpha
    orig_beta = beta

    if side == 1:
        best = -_INF
        for m in _ordered_moves(flat, side):
            flat[m] = side
            val = _alphabeta(flat, -side, depth - 1, alpha, beta)
            flat[m] = 0

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = _INF
        for m in _ordered_moves(flat, side):
            flat[m] = side
            val = _alphabeta(flat, -side, depth - 1, alpha, beta)
            flat[m] = 0

            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    # Transposition table flags:
    # 0 = exact, 1 = lower bound, 2 = upper bound
    if best <= orig_alpha:
        flag = 2
    elif best >= orig_beta:
        flag = 1
    else:
        flag = 0

    _TT[key] = (depth, flag, best)
    return best


def _best_static_move(flat):
    moves = [i for i, v in enumerate(flat) if v == 0]
    if not moves:
        return 0
    return max(moves, key=lambda m: _move_score(flat, m, 1))


def _tactical_move(flat):
    """Return a forced/tactical move index if one is obvious, else None."""
    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return None

    # Win immediately.
    wins = _immediate_winning_moves(flat, 1)
    if wins:
        return max(wins, key=lambda m: _BASE[m])

    # Block opponent's immediate win.
    blocks = _immediate_winning_moves(flat, -1)
    if blocks:
        return max(blocks, key=lambda m: _BASE[m])

    # Create an unavoidable double threat.
    best_fork = None
    best_fork_count = 0
    for m in empties:
        flat[m] = 1
        cnt = _count_immediate_after(flat, 1)
        flat[m] = 0
        if cnt > best_fork_count or (cnt == best_fork_count and best_fork is not None and _BASE[m] > _BASE[best_fork]):
            best_fork_count = cnt
            best_fork = m
    if best_fork is not None and best_fork_count >= 2:
        return best_fork

    # Stop opponent's single obvious fork.
    opponent_forks = []
    for m in empties:
        flat[m] = -1
        cnt = _count_immediate_after(flat, -1)
        flat[m] = 0
        if cnt >= 2:
            opponent_forks.append(m)

    if len(opponent_forks) == 1:
        return opponent_forks[0]

    # If opponent has many fork squares, try to make a forcing threat.
    if len(opponent_forks) > 1:
        forcing = []
        for m in empties:
            flat[m] = 1
            cnt = _count_immediate_after(flat, 1)
            flat[m] = 0
            if cnt > 0:
                forcing.append((cnt, _BASE[m], m))
        if forcing:
            return max(forcing)[2]
        return max(opponent_forks, key=lambda m: _BASE[m])

    return None


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move as (row, col).
    """
    global _DEADLINE, _NODES, _TT

    try:
        flat = [int(board[r][c]) for r in range(4) for c in range(4)]
    except Exception:
        return (0, 0)

    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return (0, 0)

    # Keep memory bounded.
    if len(_TT) > 350_000:
        _TT.clear()

    # Strong opening: central diagonal cells are high-value and symmetric.
    if len(empties) == 16:
        return (1, 1)

    # If we somehow have no mark yet, take the best central/control square.
    if flat.count(1) == 0:
        m = _best_static_move(flat)
        return divmod(m, 4)

    # Forced tactical moves should not be delayed by search.
    tm = _tactical_move(flat)
    if tm is not None and flat[tm] == 0:
        return divmod(tm, 4)

    # Safe fallback before starting timed search.
    best_move = _best_static_move(flat)

    _DEADLINE = perf_counter() + _TIME_LIMIT
    _NODES = 0

    try:
        max_depth = len(empties)

        for depth in range(1, max_depth + 1):
            root_moves = _ordered_moves(flat, 1)
            current_best = best_move
            current_val = -_INF

            alpha = -_INF
            beta = _INF

            for m in root_moves:
                _check_time()
                if flat[m] != 0:
                    continue

                flat[m] = 1
                val = _alphabeta(flat, -1, depth - 1, alpha, beta)
                flat[m] = 0

                if val > current_val or (val == current_val and _BASE[m] > _BASE[current_best]):
                    current_val = val
                    current_best = m

                if val > alpha:
                    alpha = val

            # Only accept a depth once fully completed.
            best_move = current_best

            # Found a forced result or searched to the end.
            if abs(current_val) >= _WIN or depth == max_depth:
                break

    except _Timeout:
        pass
    except Exception:
        # Never risk returning an illegal/non-move because of an unexpected issue.
        pass

    if 0 <= best_move < 16 and flat[best_move] == 0:
        return divmod(best_move, 4)

    # Absolute final legality fallback.
    for i, v in enumerate(flat):
        if v == 0:
            return divmod(i, 4)

    return (0, 0)
