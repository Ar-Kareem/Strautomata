
import time

_WIN_MASKS = []
_seen = set()
_dirs = [(dx,dy,dz) for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1) if not (dx==0 and dy==0 and dz==0)]
for _x in range(3):
    for _y in range(3):
        for _z in range(3):
            for _dx,_dy,_dz in _dirs:
                _x2=_x+_dx; _y2=_y+_dy; _z2=_z+_dz
                _x3=_x+2*_dx; _y3=_y+2*_dy; _z3=_z+2*_dz
                if 0<=_x2<3 and 0<=_y2<3 and 0<=_z2<3 and 0<=_x3<3 and 0<=_y3<3 and 0<=_z3<3:
                    _a=_x*9+_y*3+_z; _b=_x2*9+_y2*3+_z2; _c=_x3*9+_y3*3+_z3
                    _mask=(1<<_a)|(1<<_b)|(1<<_c)
                    if _mask not in _seen:
                        _seen.add(_mask)
                        _WIN_MASKS.append(_mask)
WIN_MASKS = _WIN_MASKS
CELL_MASKS = [[] for _ in range(27)]
for _m in WIN_MASKS:
    for _c in range(27):
        if (_m>>_c)&1:
            CELL_MASKS[_c].append(_m)
CELL_SCORE = [len(l) for l in CELL_MASKS]
BIT_TO_COORD = [(c//9,(c//3)%3,c%3) for c in range(27)]
CENTER_IDX = 13
CORNERS = [0,2,6,8,18,20,24,26]
WIN_VAL = 10000
INF_VAL = 20000

def _evaluate(cur, opp):
    s = 0
    for m in WIN_MASKS:
        cm = cur & m
        if cm:
            if opp & m:
                continue
            if cm == m:
                return 10000
            if cm & (cm-1):
                s += 100
            else:
                s += 1
        else:
            om = opp & m
            if om == 0:
                continue
            if om == m:
                return -10000
            if om & (om-1):
                s -= 100
            else:
                s -= 1
    return s

class _TO(Exception):
    pass

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        my = 0
        opp = 0
        empties = []
        for i in range(3):
            Bi = board[i]
            for j in range(3):
                Bij = Bi[j]
                for k in range(3):
                    v = Bij[k]
                    idx = i*9+j*3+k
                    if v == 1:
                        my |= (1 << idx)
                    elif v == -1:
                        opp |= (1 << idx)
                    else:
                        empties.append(idx)
        if not empties:
            return (0,0,0)
        # immediate win
        for c in empties:
            bit = 1 << c
            for m in CELL_MASKS[c]:
                if (my & m) == (m ^ bit):
                    return BIT_TO_COORD[c]
        # opponent immediate threats
        opp_threats = []
        for c in empties:
            bit = 1 << c
            for m in CELL_MASKS[c]:
                if (opp & m) == (m ^ bit):
                    opp_threats.append(c)
                    break
            if len(opp_threats) >= 2:
                break
        if opp_threats:
            return BIT_TO_COORD[opp_threats[0]]
        empties_set = set(empties)
        if CENTER_IDX in empties_set:
            return (1,1,1)
        if len(empties) >= 24:
            for cc in CORNERS:
                if cc in empties_set:
                    return BIT_TO_COORD[cc]
        # heuristic ordering
        scored = []
        for c in empties:
            nm = my | (1 << c)
            sc = _evaluate(nm, opp)
            scored.append((sc, CELL_SCORE[c], c))
        scored.sort(reverse=True)
        ordered = [c for _,_,c in scored]
        best_move = ordered[0]
        n = len(empties)
        if n > 22:
            max_depth = 3
        elif n > 16:
            max_depth = 4
        elif n > 10:
            max_depth = 5
        else:
            max_depth = 7
        if max_depth > n:
            max_depth = n
        deadline = time.perf_counter() + 0.88
        nodes = [0]

        def _negamax(cur, op, empt, depth, alpha, beta):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
                raise _TO()
            for cc in empt:
                b = 1 << cc
                for mm in CELL_MASKS[cc]:
                    if (cur & mm) == (mm ^ b):
                        return WIN_VAL + depth
            thr = None
            cnt = 0
            for cc in empt:
                b = 1 << cc
                is_thr = False
                for mm in CELL_MASKS[cc]:
                    if (op & mm) == (mm ^ b):
                        is_thr = True
                        break
                if is_thr:
                    cnt += 1
                    thr = cc
                    if cnt >= 2:
                        return -WIN_VAL - depth
            if cnt == 1:
                b = 1 << thr
                ncur = cur | b
                nempt = [e for e in empt if e != thr]
                if depth <= 0:
                    return _evaluate(ncur, op)
                sc = -_negamax(op, ncur, nempt, depth-1, -beta, -alpha)
                return sc
            if depth <= 0:
                return _evaluate(cur, op)
            if not empt:
                return 0
            best = -INF_VAL
            for ii, cc in enumerate(empt):
                b = 1 << cc
                ncur = cur | b
                nempt = empt[:ii] + empt[ii+1:]
                sc = -_negamax(op, ncur, nempt, depth-1, -beta, -alpha)
                if sc > best:
                    best = sc
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        break
            return best

        for depth in range(1, max_depth+1):
            if time.perf_counter() > deadline - 0.05:
                break
            try:
                cur_best = best_move
                cur_score = -INF_VAL
                alpha = -INF_VAL
                for cc in list(ordered):
                    if time.perf_counter() > deadline - 0.02:
                        raise _TO()
                    nm = my | (1 << cc)
                    nempt = [e for e in ordered if e != cc]
                    sc = -_negamax(opp, nm, nempt, depth-1, -INF_VAL, -alpha)
                    if sc > cur_score:
                        cur_score = sc
                        cur_best = cc
                        if sc > alpha:
                            alpha = sc
                    if cur_score >= WIN_VAL:
                        break
                best_move = cur_best
                if best_move in ordered:
                    ordered.remove(best_move)
                    ordered.insert(0, best_move)
                if cur_score >= WIN_VAL - 10:
                    break
            except _TO:
                break
        return BIT_TO_COORD[best_move]
    except Exception:
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            return (i,j,k)
        except Exception:
            pass
        return (0,0,0)
