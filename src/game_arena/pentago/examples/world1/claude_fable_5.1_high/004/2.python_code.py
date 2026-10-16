
import time

ALL = (1 << 36) - 1
INF = float('inf')


def _b(r, c):
    return 1 << (r * 6 + c)


QORIG = ((0, 0), (0, 3), (3, 0), (3, 3))
QMASK = []
NQMASK = []
BASE = []
DEST = []
ROT = []
for _q, (_r0, _c0) in enumerate(QORIG):
    _mask = 0
    for _i in range(3):
        for _j in range(3):
            _mask |= _b(_r0 + _i, _c0 + _j)
    QMASK.append(_mask)
    NQMASK.append(ALL ^ _mask)
    BASE.append(_r0 * 6 + _c0)
    _dl = list(range(36))
    _dr = list(range(36))
    for _i in range(3):
        for _j in range(3):
            _src = (_r0 + _i) * 6 + (_c0 + _j)
            _dl[_src] = (_r0 + 2 - _j) * 6 + (_c0 + _i)      # anticlockwise (L)
            _dr[_src] = (_r0 + _j) * 6 + (_c0 + 2 - _i)      # clockwise (R)
    DEST.append((_dl, _dr))
    _tabs = []
    for _d in range(2):
        _dest = DEST[_q][_d]
        _tab = [0] * 512
        for _v in range(512):
            _out = 0
            for _k in range(9):
                if (_v >> _k) & 1:
                    _i, _j = divmod(_k, 3)
                    _out |= 1 << _dest[(_r0 + _i) * 6 + (_c0 + _j)]
            _tab[_v] = _out
        _tabs.append(_tab)
    ROT.append(_tabs)

HM = 0
VM = 0
D1M = 0
D2M = 0
for _r in range(6):
    HM |= _b(_r, 0) | _b(_r, 1)
for _c in range(6):
    VM |= _b(0, _c) | _b(1, _c)
for _r in range(2):
    for _c in range(2):
        D1M |= _b(_r, _c)
    for _c in (4, 5):
        D2M |= _b(_r, _c)

_L = []
for _r in range(6):
    for _c in range(2):
        _L.append(sum(_b(_r, _c + i) for i in range(5)))
for _c in range(6):
    for _r in range(2):
        _L.append(sum(_b(_r + i, _c) for i in range(5)))
for _r in range(2):
    for _c in range(2):
        _L.append(sum(_b(_r + i, _c + i) for i in range(5)))
    for _c in (4, 5):
        _L.append(sum(_b(_r + i, _c - i) for i in range(5)))
LINES = tuple(_L)

try:
    bitcount = int.bit_count
except AttributeError:
    def bitcount(x):
        return bin(x).count('1')

WM = (0, 1, 4, 16, 5000, 100000, 100000, 100000)
WO = (0, 1, 4, 16, 600, 100000, 100000, 100000)
PEN = 600
DIRS4 = ((1, HM), (6, VM), (7, D1M), (5, D2M))


def rot(b, q, d):
    base = BASE[q]
    v = ((b >> base) & 7) | (((b >> (base + 6)) & 7) << 3) | (((b >> (base + 12)) & 7) << 6)
    return (b & NQMASK[q]) | ROT[q][d][v]


def five(b):
    if b & (b >> 1) & (b >> 2) & (b >> 3) & (b >> 4) & HM:
        return True
    if b & (b >> 6) & (b >> 12) & (b >> 18) & (b >> 24) & VM:
        return True
    if b & (b >> 7) & (b >> 14) & (b >> 21) & (b >> 28) & D1M:
        return True
    if b & (b >> 5) & (b >> 10) & (b >> 15) & (b >> 20) & D2M:
        return True
    return False


def has_open4(m, o):
    for s, M in DIRS4:
        x1 = m >> s
        x2 = m >> (2 * s)
        x3 = m >> (3 * s)
        x4 = m >> (4 * s)
        a = m & x1
        b = x2 & x3
        g = ((a & b) | (a & x4 & (x2 | x3)) | (b & x4 & (m | x1))) & M
        if g:
            oo = o | (o >> s) | (o >> (2 * s)) | (o >> (3 * s)) | (o >> (4 * s))
            if g & ~oo:
                return True
    return False


def can_win(me, op):
    # can 'me' (to move) win immediately?
    for q in range(4):
        for d in (0, 1):
            rm = rot(me, q, d)
            ro = rot(op, q, d)
            if five(ro):
                continue
            if five(rm) or has_open4(rm, ro):
                return True
    return False


def evaluate(me, op):
    s = 0
    for L in LINES:
        a = L & me
        if a:
            if not (L & op):
                s += WM[bitcount(a)]
        else:
            b = L & op
            if b:
                s -= WO[bitcount(b)]
    return s


def gen_moves(me, op):
    emp = ALL ^ (me | op)
    res = []
    seen = set()
    for q in range(4):
        r0 = rot(me, q, 0)
        o0 = rot(op, q, 0)
        r1 = rot(me, q, 1)
        o1 = rot(op, q, 1)
        if r0 == r1 and o0 == o1:
            dirs = ((0, r0, o0),)
        else:
            dirs = ((0, r0, o0), (1, r1, o1))
        for d, rm, ro in dirs:
            dest = DEST[q][d]
            e = emp
            while e:
                low = e & -e
                e ^= low
                cell = low.bit_length() - 1
                nm = rm | (1 << dest[cell])
                key = (nm, ro)
                if key in seen:
                    continue
                seen.add(key)
                res.append((nm, ro, q, d, cell))
    return res


def _mstr(m):
    cell = m[4]
    return "%d,%d,%d,%s" % (cell // 6 + 1, cell % 6 + 1, m[2], 'L' if m[3] == 0 else 'R')


def forced_win(nm, no, killers, deadline):
    # position after my move; opponent to move. True if every reply leaves me a win-in-one.
    emp = ALL ^ (nm | no)
    for (kq, kd, kc) in killers:
        if (emp >> kc) & 1:
            rm = rot(nm, kq, kd)
            no2 = rot(no, kq, kd) | (1 << DEST[kq][kd][kc])
            if not can_win(rm, no2):
                return False
    cnt = 0
    for q in range(4):
        r0 = rot(nm, q, 0)
        o0 = rot(no, q, 0)
        r1 = rot(nm, q, 1)
        o1 = rot(no, q, 1)
        if r0 == r1 and o0 == o1:
            dirs = ((0, r0, o0),)
        else:
            dirs = ((0, r0, o0), (1, r1, o1))
        for d, rm, ro in dirs:
            dest = DEST[q][d]
            e = emp
            while e:
                low = e & -e
                e ^= low
                cell = low.bit_length() - 1
                no2 = ro | (1 << dest[cell])
                if not can_win(rm, no2):
                    k = (q, d, cell)
                    if k not in killers:
                        killers.insert(0, k)
                        del killers[4:]
                    return False
                cnt += 1
                if not (cnt & 15) and time.perf_counter() > deadline:
                    return False
    return True


def _smart(you, opponent, t0):
    me = 0
    op = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if yr[c]:
                me |= 1 << (r * 6 + c)
            if orow[c]:
                op |= 1 << (r * 6 + c)

    moves = gen_moves(me, op)
    if not moves:
        return None

    draw_move = None
    for m in moves:
        if five(m[0]):
            if not five(m[1]):
                return _mstr(m)
            elif draw_move is None:
                draw_move = _mstr(m)

    safe = []
    for m in moves:
        nm, no = m[0], m[1]
        if five(no):
            continue
        if can_win(no, nm):
            continue
        safe.append(m)

    if not safe:
        if draw_move is not None:
            return draw_move
        cand = [m for m in moves if not five(m[1])] or moves
        best = max(cand, key=lambda m: evaluate(m[0], m[1]))
        return _mstr(best)

    scored = sorted(safe, key=lambda m: -evaluate(m[0], m[1]))
    if len(scored) == 1:
        return _mstr(scored[0])

    # forced win search (3 plies)
    fw_deadline = t0 + 0.30
    killers = []
    for m in scored:
        if time.perf_counter() > fw_deadline:
            break
        nm, no = m[0], m[1]
        if not can_win(nm, no):
            continue
        if forced_win(nm, no, killers, fw_deadline):
            return _mstr(m)

    # depth-2 alpha-beta
    DEADLINE = t0 + 0.72
    best_val = -INF
    best_ms = _mstr(scored[0])
    killer = None
    evals = 0
    timeout = False
    for m in scored:
        nm, no = m[0], m[1]
        emp = ALL ^ (nm | no)
        val = INF
        seen = set()
        cut = False
        if killer is not None:
            kq, kd, kc = killer
            if (emp >> kc) & 1:
                rm = rot(nm, kq, kd)
                no2 = rot(no, kq, kd) | (1 << DEST[kq][kd][kc])
                v = evaluate(rm, no2)
                if v <= best_val:
                    continue
                if v < 4000 and can_win(no2, rm):
                    v -= PEN
                    if v <= best_val:
                        continue
                val = v
                seen.add((rm, no2))
        for q in range(4):
            r0 = rot(nm, q, 0)
            o0 = rot(no, q, 0)
            r1 = rot(nm, q, 1)
            o1 = rot(no, q, 1)
            if r0 == r1 and o0 == o1:
                dirs = ((0, r0, o0),)
            else:
                dirs = ((0, r0, o0), (1, r1, o1))
            for d, rm, ro in dirs:
                dest = DEST[q][d]
                e = emp
                while e:
                    low = e & -e
                    e ^= low
                    cell = low.bit_length() - 1
                    no2 = ro | (1 << dest[cell])
                    key = (rm, no2)
                    if key in seen:
                        continue
                    seen.add(key)
                    v = evaluate(rm, no2)
                    evals += 1
                    if v < val:
                        if v > best_val and v < 4000 and can_win(no2, rm):
                            v -= PEN
                        val = v
                        if v <= best_val:
                            killer = (q, d, cell)
                            cut = True
                            break
                    if not (evals & 63) and time.perf_counter() > DEADLINE:
                        timeout = True
                        break
                if cut or timeout:
                    break
            if cut or timeout:
                break
        if timeout:
            break
        if cut:
            continue
        if val > best_val:
            best_val = val
            best_ms = _mstr(m)
    return best_ms


def policy(you, opponent) -> str:
    t0 = time.perf_counter()
    fallback = None
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opponent[r][c]:
                fallback = "%d,%d,0,L" % (r + 1, c + 1)
                break
        if fallback is not None:
            break
    if fallback is None:
        fallback = "1,1,0,L"
    try:
        res = _smart(you, opponent, t0)
        if res is None:
            return fallback
        return res
    except Exception:
        return fallback
