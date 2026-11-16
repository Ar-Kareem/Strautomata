
import time
import numpy as np

# ================= Static geometry for a 4x4 box grid (5x5 dots) =================
# Edge ids:
#   horizontal edge (r, c), r in 0..4, c in 0..3 -> id = r*4 + c       (0..19)
#   vertical   edge (r, c), r in 0..3, c in 0..4 -> id = 20 + r*5 + c  (20..39)
# Box (i, j), i,j in 0..3 uses H(i,j), H(i+1,j), V(i,j), V(i,j+1).

_BOX_EDGES = []
for _i in range(4):
    for _j in range(4):
        _BOX_EDGES.append((
            _i * 4 + _j,            # top    H(i, j)
            (_i + 1) * 4 + _j,      # bottom H(i+1, j)
            20 + _i * 5 + _j,       # left   V(i, j)
            20 + _i * 5 + _j + 1,   # right  V(i, j+1)
        ))

BOX_MASK = [0] * 16
_edge_boxes = [[] for _ in range(40)]
for _b in range(16):
    _m = 0
    for _e in _BOX_EDGES[_b]:
        _m |= (1 << _e)
        _edge_boxes[_e].append(_b)
    BOX_MASK[_b] = _m

# Box masks adjacent to each edge (1 box for border edges, 2 for interior).
EDGE_BM = [tuple(BOX_MASK[b] for b in _edge_boxes[e]) for e in range(40)]
NB = [len(_edge_boxes[e]) for e in range(40)]
FULL_MASK = (1 << 40) - 1


def _move_str(e):
    if e < 20:
        return "%d,%d,H" % (e >> 2, e & 3)
    v = e - 20
    return "%d,%d,V" % (v // 5, v % 5)


MOVE_STR = [_move_str(e) for e in range(40)]

try:
    _pop = int.bit_count
except AttributeError:  # older Python fallback
    def _pop(x):
        return bin(x).count("1")

_SC = 20          # score units per box (tie-breaks live below this scale)
_INF = 10 ** 7


class _Timeout(Exception):
    pass


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    start = time.perf_counter()
    deadline = start + 0.85

    # ---------- Parse the board into a 40-bit edge mask ----------
    mask = 0
    try:
        m = 0
        for r in range(5):
            row = horizontal[r]
            base = r * 4
            for c in range(4):
                if row[c] != 0:
                    m |= 1 << (base + c)
        for r in range(4):
            row = vertical[r]
            base = 20 + r * 5
            for c in range(5):
                if row[c] != 0:
                    m |= 1 << (base + c)
        mask = m
    except Exception:
        # Last-resort legal move scan if parsing unexpectedly fails.
        try:
            for r in range(5):
                for c in range(4):
                    if horizontal[r][c] == 0:
                        return "%d,%d,H" % (r, c)
            for r in range(4):
                for c in range(5):
                    if vertical[r][c] == 0:
                        return "%d,%d,V" % (r, c)
        except Exception:
            pass
        return "0,0,H"

    empties = FULL_MASK & ~mask
    n_empty = _pop(empties)
    if n_empty == 0:
        return "0,0,H"  # board full; should never be called

    # ---------- Move classification ----------
    # capture: completes >=1 box; safe: creates no 3-sided box; unsafe: creates one.
    def classify(pm):
        caps, safes, unsafes = [], [], []
        mm = FULL_MASK & ~pm
        while mm:
            lsb = mm & -mm
            e = lsb.bit_length() - 1
            mm ^= lsb
            c = 0
            mx = 0
            for bm in EDGE_BM[e]:
                cnt = _pop(pm & bm)
                if cnt == 3:
                    c += 1
                elif cnt > mx:
                    mx = cnt
            if c:
                caps.append((e, c))
            elif mx == 2:
                unsafes.append((e, mx))
            else:
                safes.append((e, mx))
        caps.sort(key=lambda t: (-t[1], -NB[t[0]]))
        safes.sort(key=lambda t: (t[1], NB[t[0]]))
        unsafes.sort(key=lambda t: (t[1], NB[t[0]]))
        return caps, safes, unsafes

    caps0, safes0, unsafes0 = classify(mask)
    ordered0 = ([t[0] for t in caps0] + [t[0] for t in safes0]
                + [t[0] for t in unsafes0])
    capd0 = {}
    for t in caps0:
        capd0[t[0]] = t[1]
    fallback = ordered0[0]
    if n_empty == 1:
        return MOVE_STR[fallback]

    # ---------- Horizon evaluation ----------
    # Greedily resolve every open chain, crediting all captured boxes to the
    # side to move, then subtract a tiny tie-break for 2-sided boxes.
    BM = BOX_MASK

    def evaluate(m, side):
        sm = m
        gain = 0
        while True:
            prog = False
            for b in range(16):
                bm = BM[b]
                if _pop(sm & bm) == 3:
                    sm |= bm
                    gain += 1
                    prog = True
            if not prog:
                break
        n2 = 0
        for b in range(16):
            if _pop(sm & BM[b]) == 2:
                n2 += 1
        val = gain * _SC if side == 0 else -gain * _SC
        return val - n2

    # ---------- Alpha-beta search (value = future boxes: ours minus theirs) ----------
    TT = {}
    nodes = [0]

    def search(m, side, depth, alpha, beta):
        nodes[0] += 1
        if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
            raise _Timeout()
        if m == FULL_MASK:
            return 0
        key = (m << 1) | side
        ent = TT.get(key)
        tbest = -1
        if ent is not None:
            ed, ev, ef, eb = ent
            tbest = eb
            if ed >= depth:
                if ef == 0:
                    return ev
                if ef == 1 and ev >= beta:
                    return ev
                if ef == 2 and ev <= alpha:
                    return ev
        if depth <= 0:
            return evaluate(m, side)

        caps, safes, unsafes = [], [], []
        mm = FULL_MASK & ~m
        while mm:
            lsb = mm & -mm
            e = lsb.bit_length() - 1
            mm ^= lsb
            c = 0
            mx = 0
            for bm in EDGE_BM[e]:
                cnt = _pop(m & bm)
                if cnt == 3:
                    c += 1
                elif cnt > mx:
                    mx = cnt
            if c:
                caps.append((e, c))
            elif mx == 2:
                unsafes.append((e, mx))
            else:
                safes.append((e, mx))
        caps.sort(key=lambda t: (-t[1], -NB[t[0]]))
        safes.sort(key=lambda t: (t[1], NB[t[0]]))
        unsafes.sort(key=lambda t: (t[1], NB[t[0]]))
        moves = ([t[0] for t in caps] + [t[0] for t in safes]
                 + [t[0] for t in unsafes])
        capd = {}
        for t in caps:
            capd[t[0]] = t[1]
        if tbest >= 0 and not ((m >> tbest) & 1):
            try:
                moves.remove(tbest)
                moves.insert(0, tbest)
            except ValueError:
                pass

        oa, ob = alpha, beta
        if side == 0:  # us: maximize
            value = -_INF
            bmove = moves[0]
            for e in moves:
                c = capd.get(e, 0)
                nm = m | (1 << e)
                if c:  # capture -> we move again (window shifted by the gain)
                    s = c * _SC
                    v = s + search(nm, 0, depth - 1, alpha - s, beta - s)
                else:
                    v = search(nm, 1, depth - 1, alpha, beta)
                if v > value:
                    value = v
                    bmove = e
                if v > alpha:
                    alpha = v
                if alpha >= beta:
                    break
        else:  # opponent: minimize
            value = _INF
            bmove = moves[0]
            for e in moves:
                c = capd.get(e, 0)
                nm = m | (1 << e)
                if c:  # opponent captures -> opponent moves again
                    s = c * _SC
                    v = -s + search(nm, 1, depth - 1, alpha + s, beta + s)
                else:
                    v = search(nm, 0, depth - 1, alpha, beta)
                if v < value:
                    value = v
                    bmove = e
                if v < beta:
                    beta = v
                if alpha >= beta:
                    break

        if value <= oa:
            flag = 2  # upper bound
        elif value >= ob:
            flag = 1  # lower bound
        else:
            flag = 0  # exact
        TT[key] = (depth, value, flag, bmove)
        return value

    # ---------- Iterative deepening at the root ----------
    best = fallback
    try:
        depth = 1
        while depth <= n_empty:
            alpha, beta = -_INF, _INF
            cur_best = best
            cur_val = -_INF
            if best in ordered0:
                root_moves = [best] + [e for e in ordered0 if e != best]
            else:
                root_moves = ordered0
            for e in root_moves:
                c = capd0.get(e, 0)
                nm = mask | (1 << e)
                if c:
                    s = c * _SC
                    v = s + search(nm, 0, depth - 1, alpha - s, beta - s)
                else:
                    v = search(nm, 1, depth - 1, alpha, beta)
                if v > cur_val:
                    cur_val = v
                    cur_best = e
                if v > alpha:
                    alpha = v
            best = cur_best
            TT[(mask << 1)] = (depth, cur_val, 0, best)
            depth += 1
    except _Timeout:
        pass
    except Exception:
        pass

    return MOVE_STR[best]
