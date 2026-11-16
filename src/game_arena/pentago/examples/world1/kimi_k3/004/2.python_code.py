
import time

# ------------------------------------------------------------------
# Pentago policy: bitboards + iterative-deepening alpha-beta search
# ------------------------------------------------------------------

_QO = ((0, 0), (0, 3), (3, 0), (3, 3))   # quadrant origins (r, c), 0-indexed


def _build_tables():
    """T[q][d][byte_idx][byte_val] -> 36-bit board after rotation (d: 0=L, 1=R)."""
    T = [[None, None] for _ in range(4)]
    for q in range(4):
        r0, c0 = _QO[q]
        for d in (0, 1):
            mp = {}
            for lr in range(3):
                for lc in range(3):
                    s = (r0 + lr) * 6 + (c0 + lc)
                    if d:                      # R: clockwise  (lr,lc)->(lc,2-lr)
                        nr, nc = lc, 2 - lr
                    else:                      # L: anticlockwise (lr,lc)->(2-lc,lr)
                        nr, nc = 2 - lc, lr
                    mp[s] = (r0 + nr) * 6 + (c0 + nc)
            byte_tables = []
            for bi in range(5):
                tab = [0] * 256
                for v in range(1, 256):
                    r = 0
                    for p in range(8):
                        if (v >> p) & 1:
                            g = (bi << 3) + p
                            if g < 36:
                                r |= 1 << mp.get(g, g)
                    tab[v] = r
                byte_tables.append(tab)
            T[q][d] = byte_tables
    return T


_T = _build_tables()

# ---- fast win detection via shift-and (run of 5) ----
_H = 0
for _r in range(6):
    for _c in (0, 1):
        _H |= 1 << (_r * 6 + _c)
_V = 0
for _r in (0, 1):
    for _c in range(6):
        _V |= 1 << (_r * 6 + _c)
_D1 = 0
for _r in (0, 1):
    for _c in (0, 1):
        _D1 |= 1 << (_r * 6 + _c)
_D2 = 0
for _r in (0, 1):
    for _c in (4, 5):
        _D2 |= 1 << (_r * 6 + _c)


def _won(b):
    if b & (b >> 1) & (b >> 2) & (b >> 3) & (b >> 4) & _H:
        return True
    if b & (b >> 6) & (b >> 12) & (b >> 18) & (b >> 24) & _V:
        return True
    if b & (b >> 7) & (b >> 14) & (b >> 21) & (b >> 28) & _D1:
        return True
    if b & (b >> 5) & (b >> 10) & (b >> 15) & (b >> 20) & _D2:
        return True
    return False


# ---- all 32 length-5 lines, for the evaluation function ----
def _build_lines():
    L = []
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << (r * 6 + c + k)
            L.append(m)
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + c)
            L.append(m)
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + c + k)
            L.append(m)
    for r in range(2):
        for c in (4, 5):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + c - k)
            L.append(m)
    return tuple(L)


_LINES = _build_lines()
_EV = (0, 1, 10, 100, 1500, 100000)

if hasattr(int, "bit_count"):
    _pc = int.bit_count
else:
    def _pc(x):
        return bin(x).count("1")


def _eval(my, op):
    """Line-based evaluation from `my`'s perspective (antisymmetric)."""
    s = 0
    pc = _pc
    ev = _EV
    for m in _LINES:
        a = my & m
        b = op & m
        if a:
            if not b:
                s += ev[pc(a)]
        elif b:
            s -= ev[pc(b)]
    return s


_INF = float("inf")
_WIN = 10 ** 8


class _TO(Exception):
    pass


def _rot(b, t):
    return (t[0][b & 255] | t[1][(b >> 8) & 255] | t[2][(b >> 16) & 255]
            | t[3][(b >> 24) & 255] | t[4][(b >> 32) & 255])


def _search(my, op, depth, alpha, beta, deadline, cnt):
    """Negamax alpha-beta; `my` is the side to move; score from `my`'s view."""
    cnt[0] += 1
    if (cnt[0] & 63) == 0 and time.time() > deadline:
        raise _TO
    occ = my | op
    seen = set()
    cands = []
    ap = cands.append
    T = _T
    won = _won
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        placed = my | (1 << cell)
        for q in range(4):
            tq = T[q]
            for d in (0, 1):
                t = tq[d]
                m2 = _rot(placed, t)
                o2 = _rot(op, t)
                kk = (m2, o2)
                if kk in seen:
                    continue
                seen.add(kk)
                if won(m2):
                    if won(o2):
                        ap((0, m2, o2))          # both complete a line -> draw
                    else:
                        return _WIN + depth      # immediate win: best possible
                elif won(o2):
                    ap((-_WIN - depth, m2, o2))  # move hands opponent the win
                else:
                    ap((None, m2, o2))
    if not cands:
        return 0                                 # board full -> draw

    if depth >= 2:
        ev = _eval
        keyed = [(term if term is not None else ev(m2, o2), term, m2, o2)
                 for (term, m2, o2) in cands]
        keyed.sort(key=lambda x: x[0], reverse=True)
    else:
        keyed = [(0, term, m2, o2) for (term, m2, o2) in cands]

    best = -_INF
    search = _search
    ev = _eval
    for _k, term, m2, o2 in keyed:
        if term is not None:
            s = term
        elif depth <= 1:
            s = ev(m2, o2)
        else:
            s = -search(o2, m2, depth - 1, -beta, -alpha, deadline, cnt)
        if s > best:
            best = s
        if s > alpha:
            alpha = s
            if alpha >= beta:
                break
    return best


def _to_bits(b):
    x = 0
    i = 0
    try:
        for r in range(6):
            row = b[r]
            for c in range(6):
                if int(row[c]):
                    x |= 1 << i
                i += 1
    except Exception:
        x = 0
        for i in range(36):
            if int(b[i]):
                x |= 1 << i
    return x


def _gen_root(my, op):
    occ = my | op
    seen = set()
    cands = []
    ap = cands.append
    T = _T
    won = _won
    ev = _eval
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        placed = my | (1 << cell)
        for q in range(4):
            tq = T[q]
            for d in (0, 1):
                t = tq[d]
                m2 = _rot(placed, t)
                o2 = _rot(op, t)
                kk = (m2, o2)
                if kk in seen:
                    continue
                seen.add(kk)
                mw = won(m2)
                ow = won(o2)
                if mw and ow:
                    term = 0
                elif mw:
                    term = _WIN + 100
                elif ow:
                    term = -_WIN - 100
                else:
                    term = None
                sc = term if term is not None else ev(m2, o2)
                ap([cell, q, d, m2, o2, term, sc])
    cands.sort(key=lambda c: c[6], reverse=True)
    return cands


def _root(cands, depth, deadline, cnt):
    best = -_INF
    bestmv = cands[0]
    alpha = -_INF
    search = _search
    ev = _eval
    for c in cands:
        term = c[5]
        if term is not None:
            s = term
        elif depth <= 1:
            s = ev(c[3], c[4])
        else:
            s = -search(c[4], c[3], depth - 1, -_INF, -alpha, deadline, cnt)
        c[6] = s
        if s > best:
            best = s
            bestmv = c
        if s > alpha:
            alpha = s
        if best >= _WIN:
            break
    cands.sort(key=lambda c: c[6], reverse=True)
    return best, (bestmv[0], bestmv[1], bestmv[2])


def _quick_win(my, op):
    occ = my | op
    T = _T
    won = _won
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        placed = my | (1 << cell)
        for q in range(4):
            tq = T[q]
            for d in (0, 1):
                t = tq[d]
                m2 = _rot(placed, t)
                if won(m2):
                    o2 = _rot(op, t)
                    if not won(o2):
                        return (cell, q, d)
    return None


def policy(you, opponent) -> str:
    try:
        my = _to_bits(you)
        op = _to_bits(opponent)
        occ = my | op
        empties = [i for i in range(36) if not (occ >> i) & 1]
        if not empties:
            return "1,1,0,L"

        # 1) play an immediate win if one exists
        mv = _quick_win(my, op)
        if mv is not None:
            cell, q, d = mv
            return "%d,%d,%d,%s" % (cell // 6 + 1, cell % 6 + 1, q, "R" if d else "L")

        deadline = time.time() + 0.78
        cnt = [0]

        cands = _gen_root(my, op)
        if not cands:
            cell = empties[0]
            return "%d,%d,0,L" % (cell // 6 + 1, cell % 6 + 1)
        bestmv = (cands[0][0], cands[0][1], cands[0][2])

        # 2) iterative deepening alpha-beta (width-limited at high depths)
        plan = [(1, None), (2, None), (3, None), (4, 24), (5, 16), (6, 10), (7, 8)]
        for depth, lim in plan:
            if depth > 1 and time.time() > deadline - 0.03:
                break
            cc = cands if (lim is None or len(cands) <= lim) else cands[:lim]
            try:
                val, mv = _root(cc, depth, deadline, cnt)
                bestmv = mv
                if val >= _WIN:
                    break
            except _TO:
                break

        cell, q, d = bestmv
        return "%d,%d,%d,%s" % (cell // 6 + 1, cell % 6 + 1, q, "R" if d else "L")
    except Exception:
        # last-resort fallback: first empty cell + always-legal rotation
        try:
            for r in range(6):
                for c in range(6):
                    if not int(you[r][c]) and not int(opponent[r][c]):
                        return "%d,%d,0,L" % (r + 1, c + 1)
        except Exception:
            pass
        return "1,1,0,L"
