
import time
import numpy as np

# ---------- precomputation ----------
_P = np.zeros((8, 36), dtype=np.intp)
for _q in range(4):
    _qr, _qc = 3 * (_q // 2), 3 * (_q % 2)
    for _d in range(2):
        _perm = np.arange(36)
        for _a in range(3):
            for _b in range(3):
                if _d == 0:      # L: anticlockwise  new[a][b] = old[b][2-a]
                    _si, _sj = _b, 2 - _a
                else:            # R: clockwise      new[a][b] = old[2-b][a]
                    _si, _sj = 2 - _b, _a
                _perm[(_qr + _a) * 6 + _qc + _b] = (_qr + _si) * 6 + _qc + _sj
        _P[_q * 2 + _d] = _perm
_INVP = np.argsort(_P, axis=1)

_wins = []
for _r in range(6):
    for _c in range(2):
        _wins.append([_r * 6 + _c + i for i in range(5)])
for _c in range(6):
    for _r in range(2):
        _wins.append([(_r + i) * 6 + _c for i in range(5)])
for _r in range(2):
    for _c in range(2):
        _wins.append([(_r + i) * 6 + _c + i for i in range(5)])
for _r in range(2):
    for _c in range(4, 6):
        _wins.append([(_r + i) * 6 + _c - i for i in range(5)])

_POS = np.array([[0, 1, 1, 1, 1, 0],
                 [1, 4, 2, 2, 4, 1],
                 [1, 2, 3, 3, 2, 1],
                 [1, 2, 3, 3, 2, 1],
                 [1, 4, 2, 2, 4, 1],
                 [0, 1, 1, 1, 1, 0]], dtype=np.float32).reshape(36) * 0.5

_WM = np.zeros((36, 33), dtype=np.float32)
for _i, _cells in enumerate(_wins):
    for _cell in _cells:
        _WM[_cell, _i] = 1.0
_WM[:, 32] = _POS

_W = [0.0, 1.0, 3.0, 12.0, 50.0, 0.0]
_TBL = np.zeros((6, 6), dtype=np.float32)
for _a in range(6):
    _TBL[_a, 0] = _W[_a]
    _TBL[0, _a] = -_W[_a]
_TBL[0, 0] = 0.0

_T3 = (3 ** np.arange(36, dtype=np.int64)).astype(np.int64)

_WIN = 1e6
_INF = 1e9
_BUDGET = 0.7


class _Timeout(Exception):
    pass


_TT = {}
_deadline = [0.0]


def _expand(me, op, want_keys):
    empties = np.flatnonzero((me | op) == 0)
    ne = empties.size
    n = 8 * ne
    CM = np.repeat(me[_P], ne, axis=0)
    CO = np.repeat(op[_P], ne, axis=0)
    CM[np.arange(n), _INVP[:, empties].ravel()] = 1
    cmc = CM.astype(np.float32) @ _WM
    coc = CO.astype(np.float32) @ _WM
    wm = cmc[:, :32]
    wo = coc[:, :32]
    win_me = (wm > 4.5).any(axis=1)
    win_op = (wo > 4.5).any(axis=1)
    sc = _TBL[wm.astype(np.intp), wo.astype(np.intp)].sum(axis=1).astype(np.float64) \
        + (cmc[:, 32] - coc[:, 32]).astype(np.float64)
    if want_keys:
        keys = CM.astype(np.int64) @ _T3 + 2 * (CO.astype(np.int64) @ _T3)
        uidx = np.unique(keys, return_index=True)[1]
    else:
        keys = None
        uidx = None
    return CM, CO, sc, win_me, win_op, keys, uidx, ne, empties


def _search(me, op, key, depth, alpha, beta, ply):
    if time.perf_counter() > _deadline[0]:
        raise _Timeout()
    tt = _TT.get(key)
    if tt is not None and tt[0] >= depth:
        flag, s = tt[1], tt[2]
        if flag == 0:
            return s
        if flag == 1 and s >= beta:
            return s
        if flag == 2 and s <= alpha:
            return s
    CM, CO, sc, win_me, win_op, keys, uidx, ne, _ = _expand(me, op, depth >= 2)
    if (win_me & ~win_op).any():
        return _WIN - ply
    both = win_me & win_op
    lose = win_op & ~win_me
    sc[both] = 0.0
    sc[lose] = -(_WIN - ply)
    if ne == 1:
        sc[~(win_me | win_op)] = 0.0
        return float(sc.max())
    if depth <= 1:
        return float(sc.max())
    order = uidx[np.argsort(-sc[uidx], kind='stable')]
    best = -_INF
    alpha0 = alpha
    for i in order:
        if lose[i] or both[i]:
            val = float(sc[i])
        else:
            val = -_search(CM[i], CO[i], int(keys[i]), depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (depth, flag, best)
    return best


def _fallback(you, opponent):
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opponent[r][c]:
                return "%d,%d,0,L" % (r + 1, c + 1)
    return "1,1,0,L"


def _move_str(i, ne, empties):
    k = i // ne
    j = i % ne
    e = int(empties[j])
    r, c = e // 6 + 1, e % 6 + 1
    q = k // 2
    d = 'L' if k % 2 == 0 else 'R'
    return "%d,%d,%d,%s" % (r, c, q, d)


def policy(you, opponent):
    start = time.perf_counter()
    try:
        me = np.array(you, dtype=np.int8).reshape(36)
        op = np.array(opponent, dtype=np.int8).reshape(36)
        _deadline[0] = start + _BUDGET
        _TT.clear()

        CM, CO, sc, win_me, win_op, keys, uidx, ne, empties = _expand(me, op, True)
        wonly = win_me & ~win_op
        if wonly.any():
            return _move_str(int(np.flatnonzero(wonly)[0]), ne, empties)
        both = win_me & win_op
        lose = win_op & ~win_me
        sc[both] = 0.0
        sc[lose] = -_WIN
        if ne == 1:
            sc[~(win_me | win_op)] = 0.0
            return _move_str(int(np.argmax(sc)), ne, empties)

        cand = [int(x) for x in uidx]
        vals = sc[uidx].astype(np.float64).copy()
        best_move = cand[int(np.argmax(vals))]
        best_val = float(vals.max())

        cur_best = None
        try:
            depth = 2
            while depth <= 12 and depth <= ne and abs(best_val) < _WIN - 1000:
                perm = np.argsort(-vals, kind='stable')
                newvals = np.empty_like(vals)
                cur_best = None
                cur_best_val = -_INF
                alpha = -_INF
                for pi in perm:
                    i = cand[pi]
                    if lose[i] or both[i]:
                        val = float(sc[i])
                    else:
                        val = -_search(CM[i], CO[i], int(keys[i]), depth - 1, -_INF, -alpha, 1)
                    newvals[pi] = val
                    if val > cur_best_val:
                        cur_best_val = val
                        cur_best = i
                        if val > alpha:
                            alpha = val
                vals = newvals
                best_move = cur_best
                best_val = cur_best_val
                cur_best = None
                depth += 1
        except _Timeout:
            if cur_best is not None:
                best_move = cur_best

        return _move_str(best_move, ne, empties)
    except Exception:
        return _fallback(you, opponent)
