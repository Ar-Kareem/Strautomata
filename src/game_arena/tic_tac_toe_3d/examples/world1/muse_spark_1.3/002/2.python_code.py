
import time

_FULL = (1 << 27) - 1
_MASKS = []
_CELL_COUNT = [0]*27
_IDX_TO_COORD = [None]*27
for _i in range(3):
    for _j in range(3):
        for _k in range(3):
            _idx = _i*9+_j*3+_k
            _IDX_TO_COORD[_idx] = (_i,_j,_k)

_dirs = []
for _dx in (-1,0,1):
    for _dy in (-1,0,1):
        for _dz in (-1,0,1):
            if _dx==0 and _dy==0 and _dz==0:
                continue
            if _dx>0 or (_dx==0 and _dy>0) or (_dx==0 and _dy==0 and _dz>0):
                _dirs.append((_dx,_dy,_dz))
for _dx,_dy,_dz in _dirs:
    for _x in range(3):
        for _y in range(3):
            for _z in range(3):
                _x2 = _x+2*_dx
                _y2 = _y+2*_dy
                _z2 = _z+2*_dz
                if 0 <= _x2 < 3 and 0 <= _y2 < 3 and 0 <= _z2 < 3:
                    _cells = [(_x+t*_dx,_y+t*_dy,_z+t*_dz) for t in range(3)]
                    _m = 0
                    for (_a,_b,_c) in _cells:
                        _m |= 1 << (_a*9+_b*3+_c)
                    if _m not in _MASKS:
                        _MASKS.append(_m)
# cell line counts
for _m in _MASKS:
    for _idx in range(27):
        if (_m >> _idx) & 1:
            _CELL_COUNT[_idx] += 1
_PRIORITY_ORDER = sorted(range(27), key=lambda x: _CELL_COUNT[x], reverse=True)

try:
    _ = (1).bit_count()
    def _popcnt(x):
        return x.bit_count()
except AttributeError:
    def _popcnt(x):
        return bin(x).count("1")

def _is_win(bits):
    for m in _MASKS:
        if (bits & m) == m:
            return True
    return False

def _winning_moves(p, o):
    res = []
    for m in _MASKS:
        if (o & m) == 0:
            pm = p & m
            if _popcnt(pm) == 2:
                e = m ^ pm
                idx = e.bit_length() - 1
                res.append(idx)
    return res

def _evaluate(my, opp):
    s = 0
    for m in _MASKS:
        mi = my & m
        oi = opp & m
        if mi and oi:
            continue
        if mi:
            if mi == m:
                return 10000
            c = _popcnt(mi)
            if c == 2:
                s += 100
            elif c == 1:
                s += 1
        elif oi:
            if oi == m:
                return -10000
            c = _popcnt(oi)
            if c == 2:
                s -= 120
            elif c == 1:
                s -= 1
    return s

class _Timeout(Exception):
    pass

WIN = 10000
INF = 10**9

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        t0 = time.time()
        deadline = t0 + 0.85
        my = 0
        opp = 0
        for i in range(3):
            bi = board[i]
            for j in range(3):
                bj = bi[j]
                for k in range(3):
                    v = bj[k]
                    if v == 1:
                        my |= 1 << (i*9+j*3+k)
                    elif v == -1:
                        opp |= 1 << (i*9+j*3+k)
        empty_mask = _FULL ^ (my | opp)
        if empty_mask == 0:
            return (0, 0, 0)
        empty = [idx for idx in range(27) if (empty_mask >> idx) & 1]

        if len(empty) == 27:
            return (1, 1, 1)
        if len(empty) == 1:
            return _IDX_TO_COORD[empty[0]]

        mw = _winning_moves(my, opp)
        if mw:
            return _IDX_TO_COORD[mw[0]]
        ow = _winning_moves(opp, my)
        if len(ow) == 1:
            return _IDX_TO_COORD[ow[0]]
        if len(ow) > 1:
            # lost in 1, block one (any move loses)
            return _IDX_TO_COORD[ow[0]]

        # order by static priority
        empty_sorted = sorted(empty, key=lambda x: _CELL_COUNT[x], reverse=True)
        # if center free, it is usually best, keep it early (already by priority)

        n = len(empty_sorted)
        if n > 20:
            max_depth = 3
        elif n > 12:
            max_depth = 4
        elif n > 8:
            max_depth = 5
        else:
            max_depth = n

        TT = {}
        nodes = [0]
        best_move = empty_sorted[0]

        # nested negamax capturing deadline/TT
        def negamax(cur_my, cur_opp, depth, alpha, beta):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.time() >= deadline:
                raise _Timeout()
            if _is_win(cur_opp):
                return -(WIN + depth)
            if _is_win(cur_my):
                return WIN + depth
            em = _FULL ^ (cur_my | cur_opp)
            if em == 0:
                return 0
            if depth == 0:
                return _evaluate(cur_my, cur_opp)
            # immediate win shortcut
            # if cur player has immediate win, value is win
            has_win = False
            for m in _MASKS:
                if (cur_opp & m) == 0 and _popcnt(cur_my & m) == 2:
                    has_win = True
                    break
            if has_win:
                return WIN + depth - 1
            key = (cur_my, cur_opp, depth)
            if key in TT:
                return TT[key]
            best = -INF
            # generate in priority order
            for mv in _PRIORITY_ORDER:
                if (em >> mv) & 1 == 0:
                    continue
                nm = cur_my | (1 << mv)
                # quick win check to avoid extra recursion
                if _is_win(nm):
                    return WIN + depth - 1
                val = -negamax(cur_opp, nm, depth-1, -beta, -alpha)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            # store exact only if no cutoff (alpha < beta at exit means exact)
            # simplified: store best anyway as approximation for exact nodes
            # to keep correctness, store only when no cutoff
            if best <= alpha and alpha < beta:
                pass
            TT[key] = best
            return best

        ordered = empty_sorted[:]
        # iterative deepening
        for depth in range(1, max_depth+1):
            if time.time() >= deadline:
                break
            # move best to front
            if best_move in ordered:
                ordered = [best_move] + [m for m in ordered if m != best_move]
            cur_best = ordered[0]
            cur_best_score = -INF
            alpha = -INF
            beta = INF
            completed = True
            try:
                for mv in ordered:
                    if time.time() >= deadline:
                        completed = False
                        break
                    nm = my | (1 << mv)
                    if _is_win(nm):
                        return _IDX_TO_COORD[mv]
                    sc = -negamax(opp, nm, depth-1, -beta, -alpha)
                    if sc > cur_best_score:
                        cur_best_score = sc
                        cur_best = mv
                    if sc > alpha:
                        alpha = sc
                    if alpha >= beta:
                        break
            except _Timeout:
                completed = False
            if not completed:
                break
            best_move = cur_best
            # forced win found
            if cur_best_score >= WIN - 50:
                break
            # if time low, stop
            if time.time() >= deadline:
                break

        return _IDX_TO_COORD[best_move]
    except Exception:
        pass
    # fallback: first empty
    try:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
    except Exception:
        pass
    return (0, 0, 0)
