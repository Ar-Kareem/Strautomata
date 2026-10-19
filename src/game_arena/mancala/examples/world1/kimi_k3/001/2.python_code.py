
import sys
import time

sys.setrecursionlimit(1000000)

_BIG = 10 ** 9          # scale for exact terminal values (dominates heuristic eval)
_INF = float("inf")
_TIME_LIMIT = 0.90      # seconds per decision
_MAX_DEPTH = 80
_TT_MAX = 1500000       # transposition table size cap

_TT = {}
_t0 = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _eval(you, opp):
    """Heuristic value from the perspective of the player to move."""
    side = 0
    bonus = 0
    for i in range(6):
        yi = you[i]
        oi = opp[i]
        side += yi - oi
        if yi and (i + yi) % 13 == 6:      # lands exactly in own store: extra turn
            bonus += 2
        if oi and (i + oi) % 13 == 6:
            bonus -= 2
    return 4 * (you[6] - opp[6]) + side + bonus


def _apply(you, opp, m):
    """Apply move m for the player to move. Returns (new_you, new_opp, extra_turn, terminal)."""
    y = [you[0], you[1], you[2], you[3], you[4], you[5], you[6]]
    o = [opp[0], opp[1], opp[2], opp[3], opp[4], opp[5], opp[6]]
    seeds = y[m]
    y[m] = 0
    laps, rem = divmod(seeds, 13)          # 13 slots: 6 own, own store, 6 opp (skip opp store)
    if laps:
        for k in range(6):
            y[k] += laps
            o[k] += laps
        y[6] += laps
    pos = m
    for _ in range(rem):
        pos += 1
        if pos == 13:
            pos = 0
        if pos < 6:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:
            o[pos - 7] += 1
    extra = (pos == 6)
    # Capture: last seed into an own house that was empty before the drop.
    if pos < 6 and y[pos] == 1:
        oh = 5 - pos
        c = o[oh]
        if c:
            y[6] += c + 1
            o[oh] = 0
            y[pos] = 0
    sy = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    so = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]
    term = False
    if sy == 0 or so == 0:                 # game over: other side sweeps remaining seeds
        y[6] += sy
        o[6] += so
        y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0
        term = True
    return ((y[0], y[1], y[2], y[3], y[4], y[5], y[6]),
            (o[0], o[1], o[2], o[3], o[4], o[5], o[6]), extra, term)


def _ordered_moves(you, opp, tt_move):
    """Return (score, move) pairs sorted best-first."""
    ms = []
    for i in range(6):
        s = you[i]
        if s == 0:
            continue
        last = (i + s) % 13
        if last == 6:
            sc = 100000 + s                                   # extra turn
        elif last < 6 and s < 13 and you[last] == 0 and opp[5 - last] > 0:
            sc = 50000 + opp[5 - last]                        # capture
        else:
            sc = (i + s) // 13                                # store passes
        if i == tt_move:
            sc += 10000000                                    # TT move first
        ms.append((sc, i))
    ms.sort(reverse=True)
    return ms


def _search(you, opp, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 4095) == 0 and time.perf_counter() - _t0 > _TIME_LIMIT:
        raise _Timeout()
    if depth <= 0:
        return _eval(you, opp)
    key = you + opp
    ent = _TT.get(key)
    tt_move = -1
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        tt_move = em
    alpha0 = alpha
    beta0 = beta
    best_val = -_INF
    best_move = -1
    first = True
    for sc, m in _ordered_moves(you, opp, tt_move):
        ny, no, extra, term = _apply(you, opp, m)
        if term:
            v = (ny[6] - no[6]) * _BIG                        # exact final score diff
        elif extra:                                           # same player moves again: no depth cost
            if first:
                v = _search(ny, no, depth, alpha, beta)
            else:
                v = _search(ny, no, depth, alpha, alpha + 1)
                if alpha < v < beta:
                    v = _search(ny, no, depth, alpha, beta)
        else:                                                 # turn passes: swap perspectives
            if first:
                v = -_search(no, ny, depth - 1, -beta, -alpha)
            else:
                v = -_search(no, ny, depth - 1, -alpha - 1, -alpha)
                if alpha < v < beta:
                    v = -_search(no, ny, depth - 1, -beta, -alpha)
        first = False
        if v > best_val:
            best_val = v
            best_move = m
        if v > alpha:
            alpha = v
            if alpha >= beta:
                break
    if best_val <= alpha0:
        flag = 2          # upper bound
    elif best_val >= beta0:
        flag = 1          # lower bound
    else:
        flag = 0          # exact
    _TT[key] = (depth, best_val, flag, best_move)
    return best_val


def _root(you, opp, depth, order):
    global _nodes
    alpha = -_INF
    best_val = -_INF
    best_move = order[0]
    vals = {}
    first = True
    for m in order:
        _nodes += 1
        ny, no, extra, term = _apply(you, opp, m)
        if term:
            v = (ny[6] - no[6]) * _BIG
        elif extra:
            if first:
                v = _search(ny, no, depth, alpha, _INF)
            else:
                v = _search(ny, no, depth, alpha, alpha + 1)
                if v > alpha:
                    v = _search(ny, no, depth, alpha, _INF)
        else:
            if first:
                v = -_search(no, ny, depth - 1, -_INF, -alpha)
            else:
                v = -_search(no, ny, depth - 1, -alpha - 1, -alpha)
                if v > alpha:
                    v = -_search(no, ny, depth - 1, -_INF, -alpha)
        first = False
        vals[m] = v
        if v > best_val:
            best_val = v
            best_move = m
        if v > alpha:
            alpha = v
    return best_val, best_move, vals


def policy(you, opponent):
    global _t0, _nodes, _TT
    try:
        y = tuple(int(v) for v in you)
        o = tuple(int(v) for v in opponent)
    except Exception:
        y = tuple(you)
        o = tuple(opponent)
    legal = [i for i in range(6) if y[i] > 0]
    if not legal:
        return 0                      # per spec this never happens
    if len(legal) == 1:
        return legal[0]
    _t0 = time.perf_counter()
    _nodes = 0
    if len(_TT) > _TT_MAX:
        _TT = {}
    best_move = legal[0]
    try:
        ent = _TT.get(y + o)
        tt_move = ent[3] if ent is not None else -1
        order = [m for (_, m) in _ordered_moves(y, o, tt_move)]
        if order:
            best_move = order[0]
        depth = 1
        while depth <= _MAX_DEPTH:
            try:
                val, bm, vals = _root(y, o, depth, order)
            except _Timeout:
                break
            best_move = bm
            order = sorted(legal, key=lambda m: -vals[m])
            # stop early if every root move is an exact (terminal) result
            if all((v >= _BIG // 2) or (v <= -_BIG // 2) for v in vals.values()):
                break
            depth += 1
            if time.perf_counter() - _t0 > _TIME_LIMIT:
                break
    except Exception:
        pass
    return int(best_move)
