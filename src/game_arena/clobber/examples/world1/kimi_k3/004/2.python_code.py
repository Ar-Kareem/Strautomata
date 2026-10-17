
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

NEI = [0] * N
DIR = [["" for _ in range(N)] for __ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in ((-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEI[i] |= 1 << j
                DIR[i][j] = ch

MATE = 1_000_000
MATE_TH = MATE - 10_000
INF = 10**9
EXACT, LOWER, UPPER = 0, 1, 2
STORE_DEPTH = 127
EVAL_CLAMP = 80_000

TT = {}
HIST = {}
DEADLINE = 0.0
NODE_COUNT = 0

class SearchTimeout(Exception):
    pass

def _to_bits(board):
    b = 0
    if len(board) == ROWS and not isinstance(board[0], int):
        for r in range(ROWS):
            row = board[r]
            for c in range(COLS):
                if int(row[c]):
                    b |= 1 << (r * COLS + c)
    else:
        for i in range(N):
            if int(board[i]):
                b |= 1 << i
    return b

def _gen_moves(me, opp):
    out = []
    m = me
    while m:
        lb = m & -m
        s = lb.bit_length() - 1
        m ^= lb
        t = NEI[s] & opp
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db
            out.append((s, d))
    return out

def _do_move(me, opp, s, d):
    bs = 1 << s
    bd = 1 << d
    return ((me & ~bs) | bd), (opp & ~bd)

def _code(s, d):
    return (s << 5) | d

def _decode(code):
    return code >> 5, code & 31

def _move_str(s, d):
    return f"{s // COLS},{s % COLS},{DIR[s][d]}"

def _child_cut(cur_cut, me, opp, s, d):
    # Move s(me) -> d(opp): delete s, recolor d to me.
    a = (NEI[s] & opp).bit_count()      # cut edges removed with s
    b = (NEI[d] & me).bit_count()       # cut edges into d, including s-d
    c = (NEI[d] & opp).bit_count()      # new cut edges after d becomes me
    return cur_cut - a - b + 1 + c

def _order_moves(me, opp, moves, tt_best_code):
    cur_cut = len(moves)
    scored = []
    for s, d in moves:
        code = _code(s, d)
        cc = _child_cut(cur_cut, me, opp, s, d)
        score = -cc * 1024 + HIST.get(code, 0)
        if cc == 0:
            score += 1 << 39
        if code == tt_best_code:
            score += 1 << 40
        scored.append((score, s, d))
    scored.sort(reverse=True)
    return [(s, d) for _, s, d in scored]

def _to_store(score, ply):
    if score > MATE_TH:
        return score + ply
    if score < -MATE_TH:
        return score - ply
    return score

def _from_store(score, ply):
    if score > MATE_TH:
        return score - ply
    if score < -MATE_TH:
        return score + ply
    return score

def _tt_store(key, depth, score, flag, best_code, ply):
    old = TT.get(key)
    if old is not None:
        od, _, of, _ = old
        if od > depth:
            return
        if od == depth and of == EXACT and flag != EXACT:
            return
    TT[key] = (depth, _to_store(score, ply), flag, best_code)

def _evaluate(me, opp, moves, ply):
    cur_cut = len(moves)

    # Exact one-ply win: leave no bichromatic adjacency for the player to move.
    for s, d in moves:
        if _child_cut(cur_cut, me, opp, s, d) == 0:
            return MATE - ply - 1

    occ = me | opp
    m_tot = me.bit_count()
    o_tot = opp.bit_count()
    score = 14 * (m_tot - o_tot) + 4 * cur_cut + 3

    seen = 0
    mixed = 0
    while True:
        rest = occ & ~seen
        if not rest:
            break
        lb = rest & -rest
        st = lb.bit_length() - 1
        seen |= lb
        stack = [st]
        m = o = cut = 0
        while stack:
            x = stack.pop()
            if (me >> x) & 1:
                m += 1
                cut += (NEI[x] & opp).bit_count()
            else:
                o += 1
            nb = NEI[x] & occ & ~seen
            while nb:
                yb = nb & -nb
                y = yb.bit_length() - 1
                nb ^= yb
                seen |= yb
                stack.append(y)

        if m and o:
            mixed += 1
            diff = m - o
            score += 30 * diff + 2 * cut + 5
            if o == 1:
                score += 90      # one enemy stone can be eliminated from this component
            if m == 1:
                score -= 90      # our component is fragile
        else:
            score += m - o       # dead component: only a tiny tiebreaker

    if mixed > 1:
        score += 3 * (mixed - 1)

    if score > EVAL_CLAMP:
        return EVAL_CLAMP
    if score < -EVAL_CLAMP:
        return -EVAL_CLAMP
    return score

def _search(me, opp, depth, alpha, beta, ply):
    global NODE_COUNT
    NODE_COUNT += 1
    if (NODE_COUNT & 2047) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    occ = (me | opp).bit_count()
    if depth > occ:
        depth = occ

    key = me | (opp << N)
    ent = TT.get(key)
    tt_best_code = None
    if ent is not None:
        ed, es, ef, eb = ent
        sc = _from_store(es, ply)
        if ed >= depth:
            if ef == EXACT:
                return sc
            if ef == LOWER and sc >= beta:
                return sc
            if ef == UPPER and sc <= alpha:
                return sc
        tt_best_code = eb

    moves = _gen_moves(me, opp)
    if not moves:
        sc = -MATE + ply
        _tt_store(key, STORE_DEPTH, sc, EXACT, None, ply)
        return sc

    if depth <= 0:
        if len(moves) == 1:
            s, d = moves[0]
            nme, nopp = _do_move(me, opp, s, d)
            return -_search(nopp, nme, 0, -beta, -alpha, ply + 1)
        return _evaluate(me, opp, moves, ply)

    ordered = _order_moves(me, opp, moves, tt_best_code)
    best_sc = -INF
    best_code = None
    a0 = alpha

    for s, d in ordered:
        nme, nopp = _do_move(me, opp, s, d)
        sc = -_search(nopp, nme, depth - 1, -beta, -alpha, ply + 1)
        if sc > best_sc:
            best_sc = sc
            best_code = _code(s, d)
        if sc > alpha:
            alpha = sc
        if alpha >= beta:
            HIST[_code(s, d)] = HIST.get(_code(s, d), 0) + depth * depth
            break

    if best_sc <= a0:
        flag = UPPER
    elif best_sc >= beta:
        flag = LOWER
    else:
        flag = EXACT
    _tt_store(key, depth, best_sc, flag, best_code, ply)
    return best_sc

def _root_search(me, opp, depth):
    key = me | (opp << N)
    ent = TT.get(key)
    tt_best_code = None
    if ent is not None:
        ed, es, ef, eb = ent
        if ed >= depth and ef == EXACT and eb is not None:
            return _from_store(es, 0), _decode(eb)
        tt_best_code = eb

    moves = _gen_moves(me, opp)
    if not moves:
        return -MATE, None

    ordered = _order_moves(me, opp, moves, tt_best_code)
    alpha = -INF
    best_sc = -INF
    best_move = ordered[0]

    for s, d in ordered:
        nme, nopp = _do_move(me, opp, s, d)
        sc = -_search(nopp, nme, depth - 1, -INF, -alpha, 1)
        if sc > best_sc:
            best_sc = sc
            best_move = (s, d)
        if sc > alpha:
            alpha = sc

    _tt_store(key, depth, best_sc, EXACT, _code(*best_move), 0)
    return best_sc, best_move

def policy(you: list[int], opponent: list[int]) -> str:
    global DEADLINE, NODE_COUNT
    DEADLINE = time.perf_counter() + 0.92
    NODE_COUNT = 0

    me = _to_bits(you)
    opp = _to_bits(opponent)
    moves = _gen_moves(me, opp)

    if not moves:
        # The game should already be over; return a syntactically valid fallback.
        return "0,0,U"
    if len(moves) == 1:
        return _move_str(*moves[0])

    # Immediate winning capture, if present.
    cur_cut = len(moves)
    for s, d in moves:
        if _child_cut(cur_cut, me, opp, s, d) == 0:
            return _move_str(s, d)

    best_move = _order_moves(me, opp, moves, None)[0]
    best_sc = -INF
    max_depth = (me | opp).bit_count()

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= DEADLINE:
            break
        try:
            sc, mv = _root_search(me, opp, depth)
        except SearchTimeout:
            break
        if mv is not None:
            best_sc, best_move = sc, mv
        if sc > MATE_TH:
            break

    return _move_str(*best_move)
