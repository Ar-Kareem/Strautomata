
"""
4x4 Tic-Tac-Toe policy: iterative-deepening negamax with alpha-beta
pruning, a transposition table, history heuristic, and a line-based
evaluation function. Immediate win / forced-block shortcuts plus a hard
time deadline guarantee a strong, always-legal move.
"""

import time
import random

_WIN = 10 ** 7
_INF = 10 ** 9
_TIME_LIMIT = 0.90

# ---------- board geometry (flat index 0..15, cell = 4*r + c) ----------
_LINES = []
for _r in range(4):
    _LINES.append(tuple(_r * 4 + _c for _c in range(4)))
for _c in range(4):
    _LINES.append(tuple(_r * 4 + _c for _r in range(4)))
_LINES.append((0, 5, 10, 15))
_LINES.append((3, 6, 9, 12))
_LINES = tuple(_LINES)

_CELL_LINES = tuple(
    tuple(li for li, ln in enumerate(_LINES) if c in ln) for c in range(16)
)

_CENTER = (0, 0, 0, 0,
           0, 2, 2, 0,
           0, 2, 2, 0,
           0, 0, 0, 0)

_ATT = (0, 2, 25, 500, _WIN)   # value of my line with k pieces
_DFN = (0, 2, 35, 700, _WIN)   # value of opponent line with k pieces
_ORD_A = (0, 4, 60, 5000)      # ordering: extending my lines
_ORD_D = (0, 3, 45, 4000)      # ordering: blocking opponent lines


class _Timeout(Exception):
    pass


def _is_win(b, c, side):
    for li in _CELL_LINES[c]:
        ln = _LINES[li]
        if (b[ln[0]] == side and b[ln[1]] == side
                and b[ln[2]] == side and b[ln[3]] == side):
            return True
    return False


def _evaluate(b, side):
    opp = -side
    total = 0
    for ln in _LINES:
        ca = 0
        cb = 0
        for i in ln:
            v = b[i]
            if v == side:
                ca += 1
            elif v == opp:
                cb += 1
        if cb == 0:
            if ca:
                total += _ATT[ca]
        elif ca == 0:
            total -= _DFN[cb]
    return total


def _move_score(b, c, side, hist):
    opp = -side
    s = _CENTER[c] + hist[c]
    for li in _CELL_LINES[c]:
        ln = _LINES[li]
        ca = 0
        cb = 0
        for i in ln:
            v = b[i]
            if v == side:
                ca += 1
            elif v == opp:
                cb += 1
        if cb == 0:
            s += _ORD_A[ca]
        if ca == 0:
            s += _ORD_D[cb]
    return s


def _negamax(b, depth, alpha, beta, side, ply, tt, deadline, counter, hist):
    counter[0] += 1
    if (counter[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout

    key = tuple(b)
    ent = tt.get(key)
    tt_move = -1
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev > alpha:
                    alpha = ev
            elif ev < beta:
                beta = ev
            if alpha >= beta:
                return ev
        tt_move = em

    if depth <= 0:
        return _evaluate(b, side)

    empties = [i for i in range(16) if b[i] == 0]
    if not empties:
        return _evaluate(b, side)

    moves = sorted(empties, key=lambda c: _move_score(b, c, side, hist),
                   reverse=True)
    if tt_move >= 0 and tt_move in moves:
        moves.remove(tt_move)
        moves.insert(0, tt_move)

    best = -_INF
    best_move = moves[0]
    alpha0 = alpha
    for c in moves:
        b[c] = side
        if _is_win(b, c, side):
            val = _WIN - ply
        else:
            val = -_negamax(b, depth - 1, -beta, -alpha, -side, ply + 1,
                            tt, deadline, counter, hist)
        b[c] = 0
        if val > best:
            best = val
            best_move = c
        if val > alpha:
            alpha = val
            if alpha >= beta:
                hist[c] += depth * depth
                break

    if best <= alpha0:
        flag = 2                       # upper bound
    elif best >= beta:
        flag = 1                       # lower bound
    else:
        flag = 0                       # exact
    tt[key] = (depth, best, flag, best_move)
    return best


def _root(b, depth, tt, deadline, counter, hist):
    empties = [i for i in range(16) if b[i] == 0]
    moves = sorted(empties, key=lambda c: _move_score(b, c, 1, hist),
                   reverse=True)
    ent = tt.get(tuple(b))
    if ent is not None and ent[3] in moves:
        moves.remove(ent[3])
        moves.insert(0, ent[3])
    best = -_INF
    best_move = moves[0]
    alpha = -_INF
    for c in moves:
        b[c] = 1
        if _is_win(b, c, 1):
            val = _WIN
        else:
            val = -_negamax(b, depth - 1, -_INF, -alpha, -1, 1,
                            tt, deadline, counter, hist)
        b[c] = 0
        if val > best:
            best = val
            best_move = c
        if val > alpha:
            alpha = val
    return best, best_move


def _winning_moves(b, side, empties):
    res = []
    for c in empties:
        b[c] = side
        if _is_win(b, c, side):
            res.append(c)
        b[c] = 0
    return res


def policy(board):
    try:
        b = [int(board[r][c]) for r in range(4) for c in range(4)]
        empties = [i for i in range(16) if b[i] == 0]
        if not empties:
            return (0, 0)

        # Opening: claim a central square.
        if len(empties) == 16:
            return random.choice(((1, 1), (1, 2), (2, 1), (2, 2)))

        # 1) Take an immediate win.
        wins = _winning_moves(b, 1, empties)
        if wins:
            m = wins[0]
            return (m // 4, m % 4)

        # 2) Block the opponent's immediate winning square(s).
        threats = _winning_moves(b, -1, empties)
        if threats:
            m = max(set(threats), key=threats.count)
            return (m // 4, m % 4)

        # 3) Iterative-deepening search under a hard deadline.
        hist = [0] * 16
        best_move = max(empties, key=lambda c: _move_score(b, c, 1, hist))
        tt = {}
        counter = [0]
        deadline = time.perf_counter() + _TIME_LIMIT
        depth = 1
        max_depth = len(empties)
        try:
            while depth <= max_depth:
                _, m = _root(b, depth, tt, deadline, counter, hist)
                best_move = m
                depth += 1
        except _Timeout:
            pass

        return (best_move // 4, best_move % 4)
    except Exception:
        # Last-resort: return any legal cell.
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
