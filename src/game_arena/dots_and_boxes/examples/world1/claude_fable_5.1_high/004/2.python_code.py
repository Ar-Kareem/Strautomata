
import numpy as np
import time

FULL = (1 << 40) - 1
TIME_BUDGET = 0.5


def _h(r, c):
    return r * 4 + c


def _v(r, c):
    return 20 + r * 5 + c


BOX_EDGES = []
for r in range(4):
    for c in range(4):
        BOX_EDGES.append((_h(r, c), _h(r + 1, c), _v(r, c), _v(r, c + 1)))
EDGE_BOXES = [[] for _ in range(40)]
for b, es in enumerate(BOX_EDGES):
    for e in es:
        EDGE_BOXES[e].append(b)
EDGE_NAME = [""] * 40
for r in range(5):
    for c in range(4):
        EDGE_NAME[_h(r, c)] = "%d,%d,H" % (r, c)
for r in range(4):
    for c in range(5):
        EDGE_NAME[_v(r, c)] = "%d,%d,V" % (r, c)


class _Timeout(Exception):
    pass


_TT = {}
_nodes = 0
_deadline = 0.0


def _sides_of(mask):
    return [((mask >> a) & 1) + ((mask >> b) & 1) + ((mask >> c) & 1) + ((mask >> d) & 1)
            for (a, b, c, d) in BOX_EDGES]


def _classify(mask, sides):
    caps = []
    safe = []
    unsafe = []
    free = FULL & ~mask
    while free:
        low = free & -free
        e = low.bit_length() - 1
        free ^= low
        mx = 0
        for b in EDGE_BOXES[e]:
            s = sides[b]
            if s > mx:
                mx = s
        if mx == 3:
            caps.append(e)
        elif mx == 2:
            unsafe.append(e)
        else:
            safe.append(e)
    return caps, safe, unsafe


def _declines(mask, unsafe, sides):
    res = []
    for e in unsafe:
        found = False
        for b in EDGE_BOXES[e]:
            if sides[b] == 2:
                for m in BOX_EDGES[b]:
                    if m != e and not (mask >> m) & 1:
                        for b2 in EDGE_BOXES[m]:
                            if b2 != b and sides[b2] == 3:
                                found = True
                        break
        if found:
            res.append(e)
    return res


def _greedy_take(mask, sides):
    sides = sides[:]
    cnt = 0
    stack = [b for b in range(16) if sides[b] == 3]
    while stack:
        b = stack.pop()
        if sides[b] != 3:
            continue
        m = -1
        for mm in BOX_EDGES[b]:
            if not (mask >> mm) & 1:
                m = mm
                break
        if m < 0:
            continue
        mask |= 1 << m
        for b2 in EDGE_BOXES[m]:
            sides[b2] += 1
            if sides[b2] == 4:
                cnt += 1
            elif sides[b2] == 3:
                stack.append(b2)
    return cnt, mask, sides


def _evaluate(mask, sides, safe, unsafe):
    if safe:
        return 1.0 if (len(safe) & 1) else -1.0
    if not unsafe:
        return 0.0
    best = 99
    for e in unsafe:
        ns = sides[:]
        for b in EDGE_BOXES[e]:
            ns[b] += 1
        cnt, _, _ = _greedy_take(mask | (1 << e), ns)
        if cnt < best:
            best = cnt
    return -float(best)


def _search(mask, sides, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise _Timeout()
    if mask == FULL:
        return 0
    ent = _TT.get(mask)
    if ent is not None:
        tdepth, tval, tflag = ent
        if tdepth >= depth:
            if tflag == 0:
                return tval
            if tflag == 1:
                if tval > alpha:
                    alpha = tval
            else:
                if tval < beta:
                    beta = tval
            if alpha >= beta:
                return tval
    caps, safe, unsafe = _classify(mask, sides)
    if caps:
        moves = caps + _declines(mask, unsafe, sides)
    else:
        if depth <= 0:
            return _evaluate(mask, sides, safe, unsafe)
        moves = safe + unsafe
    orig_alpha = alpha
    best = -1000
    for e in moves:
        nm = mask | (1 << e)
        ns = sides[:]
        gained = 0
        for b in EDGE_BOXES[e]:
            ns[b] += 1
            if ns[b] == 4:
                gained += 1
        if gained:
            val = gained + _search(nm, ns, depth, alpha - gained, beta - gained)
        else:
            val = -_search(nm, ns, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    freecount = bin(FULL & ~mask).count("1")
    sdepth = 100 if depth >= freecount else depth
    _TT[mask] = (sdepth, best, flag)
    return best


def _root(mask, sides, depth, order):
    caps, safe, unsafe = _classify(mask, sides)
    if caps:
        moves = caps + _declines(mask, unsafe, sides)
    else:
        moves = safe + unsafe
    if not moves:
        moves = [e for e in range(40) if not (mask >> e) & 1]
    if order in moves:
        moves.remove(order)
        moves.insert(0, order)
    alpha = -1000
    beta = 1000
    best = -10000
    bestmove = moves[0]
    for e in moves:
        nm = mask | (1 << e)
        ns = sides[:]
        gained = 0
        for b in EDGE_BOXES[e]:
            ns[b] += 1
            if ns[b] == 4:
                gained += 1
        if gained:
            val = gained + _search(nm, ns, depth, alpha - gained, beta - gained)
        else:
            val = -_search(nm, ns, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            bestmove = e
            if best > alpha:
                alpha = best
    return best, bestmove


def _heuristic(mask, sides):
    caps, safe, unsafe = _classify(mask, sides)
    if caps:
        return caps[0]
    if safe:
        return safe[0]
    best = None
    bc = 99
    for e in unsafe:
        ns = sides[:]
        for b in EDGE_BOXES[e]:
            ns[b] += 1
        cnt, _, _ = _greedy_take(mask | (1 << e), ns)
        if cnt < bc:
            bc = cnt
            best = e
    if best is None:
        for e in range(40):
            if not (mask >> e) & 1:
                return e
    return best


def _policy(horizontal, vertical, capture):
    global _deadline, _nodes, _TT
    start = time.time()
    H = np.asarray(horizontal)
    V = np.asarray(vertical)
    mask = 0
    for r in range(5):
        for c in range(4):
            if H[r, c] != 0:
                mask |= 1 << _h(r, c)
    for r in range(4):
        for c in range(5):
            if V[r, c] != 0:
                mask |= 1 << _v(r, c)
    legal = [e for e in range(40) if not (mask >> e) & 1]
    if not legal:
        raise RuntimeError("no legal edge")
    sides = _sides_of(mask)
    best_move = _heuristic(mask, sides)
    if len(_TT) > 1500000:
        _TT.clear()
    _deadline = start + TIME_BUDGET
    _nodes = 0
    order = best_move
    try:
        for depth in range(1, 61):
            val, mv = _root(mask, sides, depth, order)
            best_move = mv
            order = mv
            if depth >= len(legal):
                break
    except _Timeout:
        pass
    if (mask >> best_move) & 1:
        best_move = legal[0]
    name = EDGE_NAME[best_move]
    r, c, d = name.split(",")
    r = int(r)
    c = int(c)
    if d == "H":
        if H[r, c] != 0:
            raise RuntimeError("illegal")
    else:
        if V[r, c] != 0:
            raise RuntimeError("illegal")
    return name


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        return _policy(horizontal, vertical, capture)
    except Exception:
        try:
            H = np.asarray(horizontal)
            V = np.asarray(vertical)
            for r in range(5):
                for c in range(4):
                    if H[r, c] == 0:
                        return "%d,%d,H" % (r, c)
            for r in range(4):
                for c in range(5):
                    if V[r, c] == 0:
                        return "%d,%d,V" % (r, c)
            for r in range(5):
                for c in range(5):
                    if H[r, c] == 0:
                        return "%d,%d,H" % (r, c)
                    if V[r, c] == 0:
                        return "%d,%d,V" % (r, c)
        except Exception:
            pass
        return "0,0,H"
