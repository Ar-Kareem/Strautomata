
import time

R = 5
C = 6
N = 30
FULL = (1 << N) - 1

NEI = [0] * N
DEG = [0] * N
CENT = [0] * N
ROT = [0] * N      # 180-degree rotation
VREF = [0] * N     # vertical reflection

for r in range(R):
    for c in range(C):
        i = r * C + c
        m = 0
        if r > 0:
            m |= 1 << (i - C)
        if r + 1 < R:
            m |= 1 << (i + C)
        if c > 0:
            m |= 1 << (i - 1)
        if c + 1 < C:
            m |= 1 << (i + 1)
        NEI[i] = m
        DEG[i] = m.bit_count() if hasattr(int, "bit_count") else bin(m).count("1")
        CENT[i] = -(abs(2 * r - (R - 1)) + abs(2 * c - (C - 1)))
        ROT[i] = (R - 1 - r) * C + (C - 1 - c)
        VREF[i] = r * C + (C - 1 - c)

EVEN = 0
for r in range(R):
    for c in range(C):
        if (r + c) & 1 == 0:
            EVEN |= 1 << (r * C + c)
ODD = FULL ^ EVEN

if hasattr(int, "bit_count"):
    def pop(x):
        return x.bit_count()
else:
    def pop(x):
        return bin(x).count("1")

INF = 10 ** 9
MATE = 1_000_000
EXACT, LOWER, UPPER = 0, 1, 2
TIME_LIMIT = 0.90

TT = {}
DEADLINE = 0.0
NODES = 0

class _Timeout(Exception):
    pass


def _mask(board):
    # Accept either a flat length-30 iterable or a 5x6 array-like.
    if len(board) == 30:
        it = board
    elif len(board) == 5 and hasattr(board[0], "__iter__") and not isinstance(board[0], (bytes, str)):
        it = (x for row in board for x in row)
    else:
        it = board
    m = 0
    i = 0
    for v in it:
        if v:
            m |= 1 << i
        i += 1
    return m


def _move_count(my, opp):
    c = 0
    m = my
    ne = NEI
    while m:
        lb = m & -m
        i = lb.bit_length() - 1
        m ^= lb
        c += pop(ne[i] & opp)
    return c


def _gen_moves(my, opp):
    out = []
    m = my
    ne = NEI
    while m:
        lb = m & -m
        f = lb.bit_length() - 1
        m ^= lb
        ts = ne[f] & opp
        while ts:
            b = ts & -ts
            t = b.bit_length() - 1
            ts ^= b
            out.append((f, t))
    return out


def _do_move(my, opp, f, t):
    bf = 1 << f
    bt = 1 << t
    return (my ^ bf) | bt, opp ^ bt


def _move_str(move):
    f, t = move
    r = f // C
    c = f % C
    if t == f - C:
        d = "U"
    elif t == f + C:
        d = "D"
    elif t == f + 1:
        d = "R"
    else:
        d = "L"
    return "%d,%d,%s" % (r, c, d)


def _opening_move(my, opp):
    # Full alternating board: play the unique horizontal central capture that
    # breaks both the vertical-reflection and 180-degree mirror pairings.
    if (my | opp) != FULL or (my & opp):
        return None
    if my == EVEN:
        return (14, 15)  # (2,2) -> (2,3)
    if my == ODD:
        return (15, 14)  # (2,3) -> (2,2)
    return None


def _symmetry_info(my, opp):
    # Returns (proven_loss_for_side_to_move, active_symmetries).
    # A fixed-point-free involution P with my == P(opp) lets the player not to
    # move mirror every non-self move. If there is no adjacent f-P(f) pair,
    # the side to move cannot break the mirror and is lost.
    if pop(my) != pop(opp):
        return False, ()
    active = []
    for P in (ROT, VREF):
        m = my
        ok = True
        while m:
            lb = m & -m
            i = lb.bit_length() - 1
            m ^= lb
            if ((opp >> P[i]) & 1) == 0:
                ok = False
                break
        if not ok:
            continue
        active.append(P)
        m = my
        found_self = False
        while m:
            lb = m & -m
            f = lb.bit_length() - 1
            m ^= lb
            if (NEI[f] >> P[f]) & 1:
                found_self = True
                break
        if not found_self:
            return True, active
    return False, active


def _evaluate(my, opp, ply):
    mm = _move_count(my, opp)
    if mm == 0:
        return -MATE + ply
    om = _move_count(opp, my)

    mp = pop(my)
    op = pop(opp)

    m = my
    my_attacked = 0
    my_deg = 0
    while m:
        lb = m & -m
        i = lb.bit_length() - 1
        m ^= lb
        my_deg += DEG[i]
        if NEI[i] & opp:
            my_attacked += 1

    m = opp
    opp_attacked = 0
    opp_deg = 0
    while m:
        lb = m & -m
        i = lb.bit_length() - 1
        m ^= lb
        opp_deg += DEG[i]
        if NEI[i] & my:
            opp_attacked += 1

    return (135 * (mm - om)
            + 30 * (mp - op)
            + 24 * (opp_attacked - my_attacked)
            + 6 * (my_deg - opp_deg))


def _order_score(my, opp, f, t, active, ttmove):
    bt = 1 << t
    opp_after = opp ^ bt

    captured_piece_attacks = pop(NEI[t] & my)       # enemy moves removed with t
    vacated_square_attacks = pop(NEI[f] & opp)      # includes t; emptying f helps
    landing_exposure = pop(NEI[t] & opp_after)      # enemies next to our new square

    s = (captured_piece_attacks * 820
         + (vacated_square_attacks - 1) * 170
         - landing_exposure * 95
         + (DEG[t] + DEG[f]) * 24
         + CENT[t] * 4
         + CENT[f])

    if opp == bt:
        s += 10_000_000  # captured the last opposing stone

    if active:
        br = 0
        for P in active:
            if P[f] == t:
                br += 1
        s += br * 200_000

    if ttmove is not None and f == ttmove[0] and t == ttmove[1]:
        s += 5_000_000
    return s


def _search(my, opp, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise _Timeout()

    active = ()
    if ply > 0:
        sym_loss, active = _symmetry_info(my, opp)
        if sym_loss:
            return -MATE + ply

    key = (my, opp)
    ent = TT.get(key)
    ttmove = None
    alpha0, beta0 = alpha, beta
    if ent is not None:
        d, v, fl, ef, et = ent
        if d >= depth:
            if fl == EXACT:
                return v
            if fl == LOWER:
                if v > alpha:
                    alpha = v
            else:
                if v < beta:
                    beta = v
            if alpha >= beta:
                return v
        if ef >= 0:
            ttmove = (ef, et)

    if depth <= 0:
        return _evaluate(my, opp, ply)

    moves = _gen_moves(my, opp)
    if not moves:
        return -MATE + ply

    scored = []
    for f, t in moves:
        scored.append((_order_score(my, opp, f, t, active, ttmove), f, t))
    scored.sort(reverse=True)

    best = -INF
    bestf, bestt = moves[0]
    a = alpha
    for _, f, t in scored:
        nmy, nopp = _do_move(my, opp, f, t)
        v = -_search(nopp, nmy, depth - 1, -beta, -a, ply + 1)
        if v > best:
            best = v
            bestf, bestt = f, t
        if best > a:
            a = best
        if a >= beta:
            break

    if best <= alpha0:
        fl = UPPER
    elif best >= beta0:
        fl = LOWER
    else:
        fl = EXACT

    old = TT.get(key)
    if old is None or depth >= old[0] or fl == EXACT:
        TT[key] = (depth, best, fl, bestf, bestt)
    return best


def _root_search(my, opp, moves, depth):
    global NODES
    best = -INF
    bestmove = moves[0]
    a = -INF
    for f, t in moves:
        if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
            raise _Timeout()
        nmy, nopp = _do_move(my, opp, f, t)
        v = -_search(nopp, nmy, depth - 1, -INF, -a, 1)
        if v > best:
            best = v
            bestmove = (f, t)
        if v > a:
            a = v
    return best, bestmove


def policy(you: list[int], opponent: list[int]) -> str:
    global DEADLINE, NODES, TT

    my = _mask(you)
    opp = _mask(opponent)
    moves = _gen_moves(my, opp)

    if not moves:
        # The game should already be over. Return a syntactically valid fallback.
        return "0,0,U"
    if len(moves) == 1:
        return _move_str(moves[0])

    book = _opening_move(my, opp)
    if book is not None and book in moves:
        return _move_str(book)

    if len(TT) > 700_000:
        TT.clear()
    DEADLINE = time.perf_counter() + TIME_LIMIT
    NODES = 0

    # At the root we must still choose a move even in a mirror-lost position.
    _, active = _symmetry_info(my, opp)

    scored = []
    for f, t in moves:
        nmy, nopp = _do_move(my, opp, f, t)
        om = _move_count(nopp, nmy)
        if om == 0:
            s = 20_000_000
        else:
            mm = _move_count(nmy, nopp)
            exposure = pop(NEI[t] & nopp)
            br = 0
            for P in active:
                if P[f] == t:
                    br += 1
            s = (br * 300_000
                 - om * 1_000
                 + mm * 35
                 + (DEG[t] + DEG[f]) * 45
                 - exposure * 90
                 + CENT[t] * 6
                 + CENT[f] * 2)
        scored.append((s, f, t))
    scored.sort(reverse=True)
    ordered = [(f, t) for _, f, t in scored]

    bestmove = ordered[0]
    total = pop(my) + pop(opp)
    if total <= 14:
        max_depth = total + 6
    elif total <= 22:
        max_depth = 20
    else:
        max_depth = 30

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= DEADLINE:
            break
        try:
            val, mv = _root_search(my, opp, ordered, depth)
        except _Timeout:
            break
        bestmove = mv
        ordered = [mv] + [m for m in ordered if m != mv]
        if val >= MATE - 10_000:
            break

    return _move_str(bestmove)
