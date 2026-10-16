
import time
import math

# ---------------- bit constants ----------------
NOT_A = 0xFEFEFEFEFEFEFEFE  # all bits except column 0
NOT_H = 0x7F7F7F7F7F7F7F7F  # all bits except column 7
try:
    _bc = int.bit_count
except AttributeError:  # very old python fallback
    _bc = lambda x: bin(x).count("1")

INF = float("inf")
WIN = 10000000
MAX_DEPTH = 12
TIME_LIMIT = 0.85

# centralization table (index = row*8 + col)
CENT = (
    0, 1, 1, 1, 1, 1, 1, 0,
    1, 2, 3, 3, 3, 3, 2, 1,
    1, 3, 4, 5, 5, 4, 3, 1,
    1, 3, 5, 6, 6, 5, 3, 1,
    1, 3, 5, 6, 6, 5, 3, 1,
    1, 3, 4, 5, 5, 4, 3, 1,
    1, 2, 3, 3, 3, 3, 2, 1,
    0, 1, 1, 1, 1, 1, 1, 0,
)

DRS = (-1, -1, -1, 0, 0, 1, 1, 1)
DCS = (-1, 0, 1, -1, 1, -1, 0, 1)
STEPS = (-9, -8, -7, -1, 1, 7, 8, 9)
LTYPE = (2, 1, 3, 0, 0, 3, 1, 2)  # 0=row, 1=col, 2=main diag, 3=anti diag

# eval weights
COMP_W = 130
LARGEST_W = 22
CONC_W = 26
CENT_W = 2
MAT_W = 3
QUAD_W = 6
ISO_W = 12

# ---------------- mutable state (globals for speed) ----------------
pos = [0] * 64
our_mask = 0
opp_mask = 0
our_count = 0
opp_count = 0
rows = [0] * 8
cols = [0] * 8
diags = [0] * 15
adiags = [0] * 15
TT = {}
HIST = {}
KILLERS = [[None, None] for _ in range(64)]
deadline = 0.0
nodes = 0
sqrt = math.sqrt


def expand(e):
    """All 8-neighbours of the set bits of e (may exceed 64 bits; masked later)."""
    return (((e & NOT_H) << 1) | ((e & NOT_A) >> 1) | (e << 8) | (e >> 8)
            | ((e & NOT_H) << 9) | ((e & NOT_A) << 7)
            | ((e & NOT_H) >> 7) | ((e & NOT_A) >> 9))


def is_conn(mask):
    """True if all bits of mask form one 8-connected group (mask must be != 0)."""
    f = mask & -mask
    while True:
        e = f
        f = (f | ((e & NOT_H) << 1) | ((e & NOT_A) >> 1) | (e << 8) | (e >> 8)
             | ((e & NOT_H) << 9) | ((e & NOT_A) << 7)
             | ((e & NOT_H) >> 7) | ((e & NOT_A) >> 9)) & mask
        if f == e:
            return f == mask


def conn_info(mask):
    """(number of connected components, size of largest component)."""
    n = 0
    largest = 0
    m = mask
    while m:
        f = m & -m
        while True:
            e = f
            f = (f | ((e & NOT_H) << 1) | ((e & NOT_A) >> 1) | (e << 8) | (e >> 8)
                 | ((e & NOT_H) << 9) | ((e & NOT_A) << 7)
                 | ((e & NOT_H) >> 7) | ((e & NOT_A) >> 9)) & mask
            if f == e:
                break
        sz = _bc(f)
        n += 1
        if sz > largest:
            largest = sz
        m &= ~f
    return n, largest


def conc_cent(mask):
    """(mean distance of pieces to center of mass, centralization sum)."""
    m = mask
    bits = []
    sr = 0
    sc = 0
    while m:
        lsb = m & -m
        m ^= lsb
        i = lsb.bit_length() - 1
        bits.append(i)
        sr += i >> 3
        sc += i & 7
    n = len(bits)
    mr = sr / n
    mc = sc / n
    s = 0.0
    cent = 0
    for i in bits:
        r = i >> 3
        c = i & 7
        dr = r - mr
        dc = c - mc
        s += sqrt(dr * dr + dc * dc)
        cent += CENT[i]
    return s / n, cent


def gen_moves(color):
    """Generate all legal moves for `color` (1 or -1) as (from, to) index pairs."""
    res = []
    own = our_mask if color == 1 else opp_mask
    enemy = -color
    p = pos
    m = own
    while m:
        lsb = m & -m
        m ^= lsb
        f = lsb.bit_length() - 1
        r = f >> 3
        c = f & 7
        dg = r - c + 7
        ad = r + c
        for k in range(8):
            lt = LTYPE[k]
            if lt == 0:
                n = rows[r]
            elif lt == 1:
                n = cols[c]
            elif lt == 2:
                n = diags[dg]
            else:
                n = adiags[ad]
            dr = DRS[k]
            dc = DCS[k]
            r2 = r + dr * n
            if r2 < 0 or r2 > 7:
                continue
            c2 = c + dc * n
            if c2 < 0 or c2 > 7:
                continue
            step = STEPS[k]
            sq = f
            ok = True
            for _ in range(1, n):      # squares strictly between: no enemies allowed
                sq += step
                if p[sq] == enemy:
                    ok = False
                    break
            if not ok:
                continue
            t = f + step * n
            if p[t] == color:          # may not land on own piece
                continue
            res.append((f, t))
    return res


def make_move(f, t, color):
    global our_mask, opp_mask, our_count, opp_count
    captured = pos[t]
    rf = f >> 3
    cf = f & 7
    rows[rf] -= 1
    cols[cf] -= 1
    diags[rf - cf + 7] -= 1
    adiags[rf + cf] -= 1
    rt = t >> 3
    ct = t & 7
    if captured:
        rows[rt] -= 1
        cols[ct] -= 1
        diags[rt - ct + 7] -= 1
        adiags[rt + ct] -= 1
        if color == 1:
            opp_mask &= ~(1 << t)
            opp_count -= 1
        else:
            our_mask &= ~(1 << t)
            our_count -= 1
    pos[f] = 0
    pos[t] = color
    rows[rt] += 1
    cols[ct] += 1
    diags[rt - ct + 7] += 1
    adiags[rt + ct] += 1
    if color == 1:
        our_mask ^= (1 << f) | (1 << t)
    else:
        opp_mask ^= (1 << f) | (1 << t)
    return captured


def unmake_move(f, t, color, captured):
    global our_mask, opp_mask, our_count, opp_count
    rf = f >> 3
    cf = f & 7
    rt = t >> 3
    ct = t & 7
    pos[t] = 0
    rows[rt] -= 1
    cols[ct] -= 1
    diags[rt - ct + 7] -= 1
    adiags[rt + ct] -= 1
    if color == 1:
        our_mask ^= (1 << f) | (1 << t)
    else:
        opp_mask ^= (1 << f) | (1 << t)
    if captured:
        pos[t] = captured
        rows[rt] += 1
        cols[ct] += 1
        diags[rt - ct + 7] += 1
        adiags[rt + ct] += 1
        if color == 1:
            opp_mask |= 1 << t
            opp_count += 1
        else:
            our_mask |= 1 << t
            our_count += 1
    pos[f] = color
    rows[rf] += 1
    cols[cf] += 1
    diags[rf - cf + 7] += 1
    adiags[rf + cf] += 1


def evaluate(ply):
    """Static evaluation from player 1's (our) perspective."""
    if opp_count == 0:
        return WIN - ply
    if our_count == 0:
        return -(WIN - ply)
    oc, ol = conn_info(our_mask)
    pc, pl = conn_info(opp_mask)
    if oc == 1:
        return WIN - ply
    if pc == 1:
        return -(WIN - ply)
    our_conc, our_cent = conc_cent(our_mask)
    opp_conc, opp_cent = conc_cent(opp_mask)
    q1 = _bc(our_mask & (our_mask >> 1) & (our_mask >> 8) & (our_mask >> 9) & NOT_H)
    q2 = _bc(opp_mask & (opp_mask >> 1) & (opp_mask >> 8) & (opp_mask >> 9) & NOT_H)
    our_iso = _bc(our_mask & ~expand(our_mask))
    opp_iso = _bc(opp_mask & ~expand(opp_mask))
    score = ((pc - oc) * COMP_W
             + (ol - pl) * LARGEST_W
             + (our_cent - opp_cent) * CENT_W
             + (opp_count - our_count) * MAT_W
             + (q1 - q2) * QUAD_W
             + (opp_iso - our_iso) * ISO_W)
    score += int((opp_conc - our_conc) * CONC_W)
    return score


def search(depth, alpha, beta, color, ply):
    """Negamax alpha-beta; value from the side-to-move's perspective."""
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.perf_counter() > deadline:
        raise TimeoutError()
    if depth <= 0:
        return evaluate(ply) * color
    key = (our_mask, opp_mask, color)
    ent = TT.get(key)
    tt_move = None
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev <= alpha:
                return ev
            if ef == 2 and ev >= beta:
                return ev
        tt_move = em
    moves = gen_moves(color)
    if not moves:
        return -(WIN - ply)  # blocked player loses
    k1, k2 = KILLERS[ply]
    negc = -color
    p = pos
    hist = HIST

    def mkey(m):
        s = CENT[m[1]] + hist.get((color, m[0], m[1]), 0)
        if p[m[1]] == negc:
            s += 1000000
        if m == tt_move:
            s += 10000000
        elif m == k1 or m == k2:
            s += 500000
        return s

    moves.sort(key=mkey, reverse=True)
    orig_alpha = alpha
    best_val = -INF
    best_move = moves[0]
    us = color == 1
    for f, t in moves:
        captured = make_move(f, t, color)
        if us:
            mm = our_mask; om = opp_mask; ocnt = opp_count
        else:
            mm = opp_mask; om = our_mask; ocnt = our_count
        if ocnt == 0 or is_conn(mm):
            val = WIN - ply                      # mover connected (or eliminated)
        elif captured and is_conn(om):
            val = -(WIN - ply)                   # capture connected the opponent
        else:
            val = -search(depth - 1, -beta, -alpha, -color, ply + 1)
        unmake_move(f, t, color, captured)
        if val > best_val:
            best_val = val
            best_move = (f, t)
        if val > alpha:
            alpha = val
            if alpha >= beta:
                if not captured:
                    if (f, t) != k1:
                        KILLERS[ply] = [(f, t), k1]
                    hist[(color, f, t)] = hist.get((color, f, t), 0) + depth * depth
                break
    if best_val <= orig_alpha:
        fl = 1
    elif best_val >= beta:
        fl = 2
    else:
        fl = 0
    TT[key] = (depth, best_val, fl, best_move)
    return best_val


def search_root(depth):
    moves = gen_moves(1)
    if not moves:
        return None, 0
    ent = TT.get((our_mask, opp_mask, 1))
    tt_move = ent[3] if ent is not None else None
    p = pos

    def mkey(m):
        s = CENT[m[1]]
        if p[m[1]] == -1:
            s += 1000000
        if m == tt_move:
            s += 10000000
        return s

    moves.sort(key=mkey, reverse=True)
    best_move = moves[0]
    best_val = -INF
    alpha = -INF
    for f, t in moves:
        captured = make_move(f, t, 1)
        if opp_count == 0 or is_conn(our_mask):
            val = WIN - 1
        elif captured and is_conn(opp_mask):
            val = -(WIN - 1)
        else:
            val = -search(depth - 1, -INF, -alpha, -1, 1)
        unmake_move(f, t, 1, captured)
        if val > best_val:
            best_val = val
            best_move = (f, t)
        if val > alpha:
            alpha = val
    TT[(our_mask, opp_mask, 1)] = (depth, best_val, 0, best_move)
    return best_move, best_val


def policy(board):
    global our_mask, opp_mask, our_count, opp_count
    global rows, cols, diags, adiags
    global TT, HIST, KILLERS, deadline, nodes

    start = time.perf_counter()
    deadline = start + TIME_LIMIT

    # ---- parse board into bitboards + line counts ----
    our_mask = 0
    opp_mask = 0
    our_count = 0
    opp_count = 0
    rows = [0] * 8
    cols = [0] * 8
    diags = [0] * 15
    adiags = [0] * 15
    for i in range(64):
        pos[i] = 0
    for r in range(8):
        row = board[r]
        base = r * 8
        for c in range(8):
            v = row[c]
            if v:
                i = base + c
                pos[i] = 1 if v == 1 else -1
                rows[r] += 1
                cols[c] += 1
                diags[r - c + 7] += 1
                adiags[r + c] += 1
                if v == 1:
                    our_mask |= 1 << i
                    our_count += 1
                else:
                    opp_mask |= 1 << i
                    opp_count += 1

    moves = gen_moves(1)
    if not moves or our_count == 0:
        return "0,0:0,0"  # should never happen; placeholder
    f0, t0 = moves[0]
    fallback = "%d,%d:%d,%d" % (f0 >> 3, f0 & 7, t0 >> 3, t0 & 7)
    if len(moves) == 1:
        return fallback
    # already-terminal positions (game should be over): just give a legal move
    if our_count == 1 or opp_count == 0 or is_conn(our_mask) or is_conn(opp_mask):
        return fallback

    TT = {}
    HIST = {}
    KILLERS = [[None, None] for _ in range(64)]
    nodes = 0
    best_move = moves[0]
    try:
        depth = 1
        while depth <= MAX_DEPTH:
            bm, val = search_root(depth)
            if bm is not None:
                best_move = bm
            if val >= WIN - 200 or val <= -(WIN - 200):
                break  # proven win or unavoidable loss
            if time.perf_counter() > deadline - 0.05:
                break
            depth += 1
    except TimeoutError:
        pass
    except Exception:
        return fallback  # never fail to return a legal move

    f, t = best_move
    return "%d,%d:%d,%d" % (f >> 3, f & 7, t >> 3, t & 7)
