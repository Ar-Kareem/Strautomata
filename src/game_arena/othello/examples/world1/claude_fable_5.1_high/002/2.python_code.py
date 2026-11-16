
import numpy as np
import time

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INF = 10 ** 9
TIME_LIMIT = 0.7

try:
    (0).bit_count
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

# ---------- precomputed tables ----------
RAYS = []
for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    _rays = []
    for _dr, _dc in ((-1, 0), (1, 0), (0, 1), (0, -1), (-1, 1), (-1, -1), (1, 1), (1, -1)):
        _ray = []
        _rr, _cc = _r + _dr, _c + _dc
        while 0 <= _rr < 8 and 0 <= _cc < 8:
            _ray.append(1 << (_rr * 8 + _cc))
            _rr += _dr
            _cc += _dc
        if len(_ray) >= 2:
            _rays.append(_ray)
    RAYS.append(_rays)

WTABLE = [
    30, -8, 6, 4, 4, 6, -8, 30,
    -8, -14, -2, -2, -2, -2, -14, -8,
    6, -2, 2, 0, 0, 2, -2, 6,
    4, -2, 0, 0, 0, 0, -2, 4,
    4, -2, 0, 0, 0, 0, -2, 4,
    6, -2, 2, 0, 0, 2, -2, 6,
    -8, -14, -2, -2, -2, -2, -14, -8,
    30, -8, 6, 4, 4, 6, -8, 30,
]
WMASKS = {}
for _sq, _w in enumerate(WTABLE):
    if _w != 0:
        WMASKS[_w] = WMASKS.get(_w, 0) | (1 << _sq)
WMASKS = list(WMASKS.items())

# Static ordering weights (corners great, X squares bad)
SQW = [
    100, -20, 10, 5, 5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10, -2, -1, -1, -1, -1, -2, 10,
    5, -2, -1, -1, -1, -1, -2, 5,
    5, -2, -1, -1, -1, -1, -2, 5,
    10, -2, -1, -1, -1, -1, -2, 10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10, 5, 5, 10, -20, 100,
]

CORNER_BITS = [1 << 0, 1 << 7, 1 << 56, 1 << 63]
CORNER_MASK = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
# For each corner: X square bit, C square bits
CORNER_ADJ = [
    (1 << 9, (1 << 1) | (1 << 8)),
    (1 << 14, (1 << 6) | (1 << 15)),
    (1 << 49, (1 << 48) | (1 << 57)),
    (1 << 54, (1 << 55) | (1 << 62)),
]

EDGES = []
for _edge in ([r * 8 + 0 for r in range(8)], [r * 8 + 7 for r in range(8)],
              [0 * 8 + c for c in range(8)], [7 * 8 + c for c in range(8)]):
    _bits = [1 << s for s in _edge]
    _mask = 0
    for _b in _bits:
        _mask |= _b
    EDGES.append((_bits, _mask))


# ---------- core bitboard functions ----------
def gen_moves(me, opp):
    empty = ~(me | opp) & FULL
    oa = opp & NOT_A
    oh = opp & NOT_H
    # North
    x = (me >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    mv = (x >> 8) & empty
    # South
    x = (me << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    mv |= (x << 8) & empty
    # East
    x = (me << 1) & oa
    x |= (x << 1) & oa
    x |= (x << 1) & oa
    x |= (x << 1) & oa
    x |= (x << 1) & oa
    x |= (x << 1) & oa
    mv |= (x << 1) & NOT_A & empty
    # West
    x = (me >> 1) & oh
    x |= (x >> 1) & oh
    x |= (x >> 1) & oh
    x |= (x >> 1) & oh
    x |= (x >> 1) & oh
    x |= (x >> 1) & oh
    mv |= (x >> 1) & NOT_H & empty
    # North-East
    x = (me >> 7) & oa
    x |= (x >> 7) & oa
    x |= (x >> 7) & oa
    x |= (x >> 7) & oa
    x |= (x >> 7) & oa
    x |= (x >> 7) & oa
    mv |= (x >> 7) & NOT_A & empty
    # North-West
    x = (me >> 9) & oh
    x |= (x >> 9) & oh
    x |= (x >> 9) & oh
    x |= (x >> 9) & oh
    x |= (x >> 9) & oh
    x |= (x >> 9) & oh
    mv |= (x >> 9) & NOT_H & empty
    # South-East
    x = (me << 9) & oa
    x |= (x << 9) & oa
    x |= (x << 9) & oa
    x |= (x << 9) & oa
    x |= (x << 9) & oa
    x |= (x << 9) & oa
    mv |= (x << 9) & NOT_A & empty
    # South-West
    x = (me << 7) & oh
    x |= (x << 7) & oh
    x |= (x << 7) & oh
    x |= (x << 7) & oh
    x |= (x << 7) & oh
    x |= (x << 7) & oh
    mv |= (x << 7) & NOT_H & empty
    return mv


def compute_flips(me, opp, sq):
    f = 0
    for ray in RAYS[sq]:
        cap = 0
        for b in ray:
            if opp & b:
                cap |= b
            elif me & b:
                f |= cap
                break
            else:
                break
    return f


def dilate(b):
    return (b | (b >> 8) | (b << 8) | ((b << 1) & NOT_A) | ((b >> 1) & NOT_H)
            | ((b << 9) & NOT_A) | ((b >> 7) & NOT_A) | ((b << 7) & NOT_H) | ((b >> 9) & NOT_H)) & FULL


def stable_count(p, o):
    occ = p | o
    cnt = 0
    for bits, mask in EDGES:
        if (occ & mask) == mask:
            cnt += popcount(p & mask)
            continue
        if p & bits[0]:
            for b in bits:
                if p & b:
                    cnt += 1
                else:
                    break
        if p & bits[7]:
            for i in range(7, -1, -1):
                if p & bits[i]:
                    cnt += 1
                else:
                    break
    return cnt


def terminal_value(me, opp):
    return (popcount(me) - popcount(opp)) * 1000


def evaluate(me, opp):
    empty = ~(me | opp) & FULL
    ne = popcount(empty)
    my_m = gen_moves(me, opp)
    op_m = gen_moves(opp, me)
    if my_m == 0 and op_m == 0:
        return terminal_value(me, opp)
    mob = popcount(my_m) - popcount(op_m)
    pmob = popcount(dilate(opp) & empty) - popcount(dilate(me) & empty)

    pos = 0
    for w, m in WMASKS:
        pos += w * (popcount(me & m) - popcount(opp & m))
    occ = me | opp
    for i in range(4):
        if occ & CORNER_BITS[i]:
            xb, cb = CORNER_ADJ[i]
            if me & xb:
                pos += 14
            elif opp & xb:
                pos -= 14
            pos += 8 * (popcount(me & cb) - popcount(opp & cb))
    corners = popcount(me & CORNER_MASK) - popcount(opp & CORNER_MASK)
    stab = stable_count(me, opp) - stable_count(opp, me)
    disc = popcount(me) - popcount(opp)

    if ne > 40:
        wm, wp, ws, wd = 10, 4, 12, -2
    elif ne > 20:
        wm, wp, ws, wd = 8, 3, 15, 0
    else:
        wm, wp, ws = 6, 2, 18
        wd = max(0, (24 - ne)) // 2

    return wm * mob + wp * pmob + pos + 20 * corners + ws * stab + wd * disc


# ---------- search ----------
class Timeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def search(self, me, opp, depth, alpha, beta, passed):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        moves = gen_moves(me, opp)
        if moves == 0:
            if passed or gen_moves(opp, me) == 0:
                return terminal_value(me, opp)
            return -self.search(opp, me, depth, -beta, -alpha, True)
        if depth <= 0:
            return evaluate(me, opp)

        key = (me, opp)
        tt = self.tt.get(key)
        tt_move = -1
        if tt is not None:
            tdepth, tval, tflag, tmove = tt
            if tdepth >= depth:
                if tflag == 0:
                    return tval
                if tflag == 1 and tval >= beta:
                    return tval
                if tflag == 2 and tval <= alpha:
                    return tval
            tt_move = tmove

        lst = []
        b = moves
        deep = depth >= 3
        while b:
            lsb = b & -b
            sq = lsb.bit_length() - 1
            b ^= lsb
            f = compute_flips(me, opp, sq)
            nme = me | f | lsb
            nopp = opp & ~f
            if sq == tt_move:
                score = 100000
            elif deep:
                score = SQW[sq] - 6 * popcount(gen_moves(nopp, nme))
            else:
                score = SQW[sq]
            lst.append((score, sq, nme, nopp))
        lst.sort(reverse=True)

        orig_alpha = alpha
        best = -INF
        bm = -1
        for score, sq, nme, nopp in lst:
            v = -self.search(nopp, nme, depth - 1, -beta, -alpha, False)
            if v > best:
                best = v
                bm = sq
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag, bm)
        return best


def sq_to_str(sq):
    r, c = divmod(sq, 8)
    return chr(ord('a') + c) + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start = time.perf_counter()
    deadline = start + TIME_LIMIT
    me = 0
    opp = 0
    for idx in np.flatnonzero(np.asarray(you).reshape(-1)):
        me |= 1 << int(idx)
    for idx in np.flatnonzero(np.asarray(opponent).reshape(-1)):
        opp |= 1 << int(idx)

    moves = gen_moves(me, opp)
    if moves == 0:
        return "pass"

    # Build root move list with static ordering
    root = []
    b = moves
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        f = compute_flips(me, opp, sq)
        root.append((SQW[sq], sq, me | f | lsb, opp & ~f))
    root.sort(reverse=True)
    best_sq = root[0][1]
    if len(root) == 1:
        return sq_to_str(best_sq)

    empties = popcount(~(me | opp) & FULL)
    lst = [(sq, nme, nopp) for _, sq, nme, nopp in root]

    try:
        searcher = Searcher(deadline)
        depth = 1
        while depth <= empties + 1 and depth <= 60:
            iter_best = -INF
            iter_bm = -1
            alpha = -INF
            beta = INF
            scored = []
            try:
                for sq, nme, nopp in lst:
                    v = -searcher.search(nopp, nme, depth - 1, -beta, -alpha, False)
                    scored.append((v, sq, nme, nopp))
                    if v > iter_best:
                        iter_best = v
                        iter_bm = sq
                        best_sq = iter_bm  # first move completed -> at least as good as previous best
                    if v > alpha:
                        alpha = v
            except Timeout:
                break
            best_sq = iter_bm
            scored.sort(reverse=True)
            lst = [(sq, nme, nopp) for _, sq, nme, nopp in scored]
            if depth >= empties:
                break
            depth += 1
            if time.perf_counter() > deadline:
                break
    except Exception:
        pass

    # Final legality check
    if not (moves >> best_sq) & 1:
        best_sq = root[0][1]
    return sq_to_str(best_sq)
