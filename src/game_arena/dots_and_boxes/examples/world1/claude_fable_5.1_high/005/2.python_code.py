
import numpy as np
import time

# ---------------- Geometry ----------------
def _H(r, c):
    return r * 4 + c          # r in 0..4, c in 0..3

def _V(r, c):
    return 20 + r * 5 + c     # r in 0..3, c in 0..4

BOX_EDGES = []
for _r in range(4):
    for _c in range(4):
        BOX_EDGES.append((_H(_r, _c), _H(_r + 1, _c), _V(_r, _c), _V(_r, _c + 1)))
BOX_MASK = [sum(1 << e for e in be) for be in BOX_EDGES]
_EB = [[] for _ in range(40)]
for _b, _be in enumerate(BOX_EDGES):
    for _e in _be:
        _EB[_e].append(_b)
EDGE_BOXES = [tuple(x) for x in _EB]
EDGE_STR = [None] * 40
for _r in range(5):
    for _c in range(4):
        EDGE_STR[_H(_r, _c)] = "%d,%d,H" % (_r, _c)
for _r in range(4):
    for _c in range(5):
        EDGE_STR[_V(_r, _c)] = "%d,%d,V" % (_r, _c)
FULL = (1 << 40) - 1
INF = 10 ** 6

try:
    (5).bit_count()
    def _pc(x):
        return x.bit_count()
except AttributeError:
    def _pc(x):
        return bin(x).count('1')


class _Timeout(Exception):
    pass


_TT = {}
_nodes = 0
_evals = 0
_deadline = 0.0


def _sides(mask):
    return [_pc(mask & bm) for bm in BOX_MASK]


def _missing(mask, b, exclude=-1):
    for e in BOX_EDGES[b]:
        if e != exclude and not (mask >> e) & 1:
            return e
    return -1


def _other_box(e, b):
    for x in EDGE_BOXES[e]:
        if x != b:
            return x
    return -1


def _capture_phase(mask):
    """Take all forced captures. Returns (gain, mask, cands_or_None, sides, first_forced_edge)."""
    gain = 0
    first = None
    while True:
        sides = _sides(mask)
        three = [b for b in range(16) if sides[b] == 3]
        if not three:
            return gain, mask, None, sides, first
        forced = -1
        cands = []
        for A in three:
            e = _missing(mask, A)
            dd = -1
            B = _other_box(e, A)
            if B >= 0 and sides[B] == 2:
                f = _missing(mask, B, e)
                C = _other_box(f, B)
                ok = True
                if C >= 0 and sides[C] == 2:
                    g = _missing(mask, C, f)
                    D = _other_box(g, C)
                    ok = (D >= 0 and sides[D] == 3)
                if ok:
                    dd = f
            if dd < 0:
                forced = e
                break
            cands.append(e)
            cands.append(dd)
        if forced >= 0:
            if first is None:
                first = forced
            for b in EDGE_BOXES[forced]:
                if sides[b] == 3:
                    gain += 1
            mask |= 1 << forced
            continue
        seen = set()
        out = []
        for e in cands:
            if e not in seen:
                seen.add(e)
                out.append(e)
        return gain, mask, out, sides, first


def _gen_moves(mask, sides):
    parent = list(range(16))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    safe = []
    unsafe = []
    for e in range(40):
        if (mask >> e) & 1:
            continue
        bs = EDGE_BOXES[e]
        t = [b for b in bs if sides[b] == 2]
        if not t:
            safe.append(e)
        else:
            unsafe.append((e, t))
            if len(t) == 2:
                ra, rb = find(t[0]), find(t[1])
                if ra != rb:
                    parent[ra] = rb
    comps = {}
    for e, t in unsafe:
        r = find(t[0])
        lst = comps.get(r)
        if lst is None:
            comps[r] = [(e, len(t))]
        else:
            lst.append((e, len(t)))
    cnt = {}
    for b in range(16):
        if sides[b] == 2:
            r = find(b)
            cnt[r] = cnt.get(r, 0) + 1
    sacs = []
    info = []
    for r, lst in comps.items():
        L = cnt.get(r, 1)
        is_loop = (len(lst) == L)
        rep = lst[0][0]
        if L == 2:
            for e, k in lst:
                if k == 2:
                    rep = e
                    break
        sacs.append((L + (2 if is_loop else 0), rep))
        info.append((L, is_loop))
    sacs.sort(key=lambda x: x[0])
    safe.sort(key=lambda e: sum(sides[b] for b in EDGE_BOXES[e]))
    return safe, [s[1] for s in sacs], info


def _evaluate(sides, S, comps):
    R = sum(1 for s in sides if s < 4)
    LC = sum(1 for (L, lp) in comps if lp or L >= 3)
    W = R - 4 * max(LC - 1, 0)
    if W < 1:
        W = 1
    W *= 0.5
    if W > 6:
        W = 6
    return W if (S & 1) else -W


def _search(mask, depth, alpha, beta):
    global _nodes, _evals
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise _Timeout()
    if mask == FULL:
        return 0
    ent = _TT.get(mask)
    ttmove = -1
    if ent is not None:
        d, flag, val, ttmove = ent
        if d >= depth:
            if flag == 0:
                return val
            if flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
    alpha0, beta0 = alpha, beta
    ev0 = _evals
    gain, m2, cands, sides, _ = _capture_phase(mask)
    bestm = -1
    if m2 == FULL:
        value = gain
    else:
        a = alpha - gain
        b = beta - gain
        best = -INF
        if cands is not None:
            moves = cands
        else:
            safe, sacs, comps = _gen_moves(m2, sides)
            if depth <= 0 and safe:
                _evals += 1
                value = gain + _evaluate(sides, len(safe), comps)
                old = _TT.get(mask)
                if old is None or old[0] <= depth:
                    _TT[mask] = (depth, 0, value, -1)
                return value
            moves = safe + sacs
        if ttmove >= 0 and ttmove in moves:
            moves = [ttmove] + [m for m in moves if m != ttmove]
        for e in moves:
            m3 = m2 | (1 << e)
            g = 0
            for bx in EDGE_BOXES[e]:
                if (m3 & BOX_MASK[bx]) == BOX_MASK[bx]:
                    g += 1
            if g:
                v = g + _search(m3, depth, a - g, b - g)
            else:
                v = -_search(m3, depth - 1, -b, -a)
            if v > best:
                best = v
                bestm = e
            if v > a:
                a = v
            if a >= b:
                break
        value = gain + best
    exact = (_evals == ev0)
    dstore = 99 if exact else depth
    if value <= alpha0:
        flag = 2
    elif value >= beta0:
        flag = 1
    else:
        flag = 0
    old = _TT.get(mask)
    if old is None or old[0] <= dstore:
        _TT[mask] = (dstore, flag, value, bestm)
    return value


def _root_search(m2, moves, depth, mode, prev_best):
    global _evals
    if prev_best in moves:
        moves = [prev_best] + [m for m in moves if m != prev_best]
    ec0 = _evals
    a = -INF
    bestv = -INF
    bestm = moves[0]
    for e in moves:
        m3 = m2 | (1 << e)
        g = 0
        for bx in EDGE_BOXES[e]:
            if (m3 & BOX_MASK[bx]) == BOX_MASK[bx]:
                g += 1
        if mode == 'cap' and g:
            v = g + _search(m3, depth, a - g, INF)
        else:
            v = -_search(m3, depth - 1, -INF, -a)
        if v > bestv:
            bestv = v
            bestm = e
        if v > a:
            a = v
    return bestm, bestv, (_evals == ec0)


def _choose_move(mask):
    global _TT, _nodes, _evals
    if mask == FULL:
        return None
    gain, m2, cands, sides, first = _capture_phase(mask)
    if first is not None:
        return first
    if cands is not None:
        root_moves = cands
        mode = 'cap'
    else:
        safe, sacs, comps = _gen_moves(m2, sides)
        root_moves = safe + sacs
        mode = 'normal'
    if not root_moves:
        return None
    if len(root_moves) == 1:
        return root_moves[0]
    _TT = {}
    _nodes = 0
    _evals = 0
    best = root_moves[0]
    depth = 1
    while True:
        try:
            mv, val, exact = _root_search(m2, root_moves, depth, mode, best)
        except _Timeout:
            break
        best = mv
        if exact or depth > 60:
            break
        depth += 1
    return best


def _simple_fallback(mask):
    gain, m2, cands, sides, first = _capture_phase(mask)
    if first is not None:
        return first
    if cands:
        return cands[0]
    safe, sacs, comps = _gen_moves(m2, sides)
    if safe:
        return safe[0]
    if sacs:
        return sacs[0]
    for e in range(40):
        if not (mask >> e) & 1:
            return e
    return None


def _array_legal(horizontal, vertical, s):
    try:
        r, c, d = s.split(',')
        r = int(r)
        c = int(c)
        if d == 'H':
            return int(horizontal[r][c]) == 0
        return int(vertical[r][c]) == 0
    except Exception:
        return False


def _any_legal(horizontal, vertical):
    for r in range(5):
        for c in range(4):
            try:
                if int(horizontal[r][c]) == 0:
                    return "%d,%d,H" % (r, c)
            except Exception:
                pass
    for r in range(4):
        for c in range(5):
            try:
                if int(vertical[r][c]) == 0:
                    return "%d,%d,V" % (r, c)
            except Exception:
                pass
    for r in range(5):
        for c in range(5):
            try:
                if int(horizontal[r][c]) == 0:
                    return "%d,%d,H" % (r, c)
            except Exception:
                pass
            try:
                if int(vertical[r][c]) == 0:
                    return "%d,%d,V" % (r, c)
            except Exception:
                pass
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    global _deadline
    start = time.time()
    _deadline = start + 0.7
    mask = 0
    try:
        for r in range(5):
            for c in range(4):
                if int(horizontal[r][c]) != 0:
                    mask |= 1 << (r * 4 + c)
        for r in range(4):
            for c in range(5):
                if int(vertical[r][c]) != 0:
                    mask |= 1 << (20 + r * 5 + c)
    except Exception:
        return _any_legal(horizontal, vertical)
    e = None
    try:
        e = _choose_move(mask)
    except Exception:
        e = None
    if e is None:
        try:
            e = _simple_fallback(mask)
        except Exception:
            e = None
    if e is not None:
        s = EDGE_STR[e]
        if _array_legal(horizontal, vertical, s):
            return s
    return _any_legal(horizontal, vertical)
