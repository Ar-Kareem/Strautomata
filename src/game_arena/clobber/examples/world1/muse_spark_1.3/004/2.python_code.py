
import time

ROWS = 5
COLS = 6
N = 30
MATE = 100000
INF = 10**9

BIT = [1 << i for i in range(N)]
NB_MASK = [0]*N
W = [0]*N

for r in range(ROWS):
    for c in range(COLS):
        i = r*COLS + c
        m = 0
        if r > 0:
            m |= BIT[(r-1)*COLS + c]
        if r+1 < ROWS:
            m |= BIT[(r+1)*COLS + c]
        if c > 0:
            m |= BIT[r*COLS + c-1]
        if c+1 < COLS:
            m |= BIT[r*COLS + c+1]
        NB_MASK[i] = m
        # centrality: higher in centre, int only
        # 12 - (2*|r-2| + |2*c-5|)
        W[i] = 12 - (2*abs(r-2) + abs(2*c-5))

try:
    _has_bc = hasattr(int, "bit_count")
except Exception:
    _has_bc = False

def _popcnt(x: int) -> int:
    if _has_bc:
        return x.bit_count()
    return bin(x).count("1")

def _count_moves(tm: int, ot: int) -> int:
    cnt = 0
    b = tm
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        b ^= lsb
        cnt += _popcnt(NB_MASK[src] & ot)
    return cnt

def _gen_moves(tm: int, ot: int):
    moves = []
    b = tm
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        b ^= lsb
        adj = NB_MASK[src] & ot
        while adj:
            lsb2 = adj & -adj
            dst = lsb2.bit_length() - 1
            adj ^= lsb2
            moves.append((src, dst))
    return moves

def _sum_w(bits: int) -> int:
    s = 0
    b = bits
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        b ^= lsb
        s += W[idx]
    return s

def _to_bits(board) -> int:
    bits = 0
    try:
        import numpy as _np
        a = _np.asarray(board)
        flat = a.flat
        for idx, v in enumerate(flat):
            if v:
                if idx < N:
                    bits |= BIT[idx]
        return bits
    except Exception:
        pass
    # pure python fallback: assume 5x6 nested list
    try:
        for r in range(ROWS):
            row = board[r]
            for c in range(COLS):
                try:
                    v = row[c]
                except Exception:
                    continue
                if v:
                    bits |= BIT[r*COLS + c]
    except Exception:
        # flat list fallback
        try:
            for idx, v in enumerate(board):
                if v:
                    bits |= BIT[idx]
        except Exception:
            pass
    return bits

class _Timeout(Exception):
    pass

def policy(you, opponent) -> str:
    start = time.perf_counter()
    deadline = start + 0.85

    def _check_timeout():
        if time.perf_counter() > deadline:
            raise _Timeout()

    my = _to_bits(you)
    ot = _to_bits(opponent)

    moves = _gen_moves(my, ot)
    if not moves:
        return '0,0,U'
    if len(moves) == 1:
        src, dst = moves[0]
        r, c = divmod(src, COLS)
        r2, c2 = divmod(dst, COLS)
        if r2 == r-1:
            d = 'U'
        elif r2 == r+1:
            d = 'D'
        elif c2 == c+1:
            d = 'R'
        else:
            d = 'L'
        return f'{r},{c},{d}'

    # evaluation from perspective of player to move
    def _evaluate(tm: int, other: int) -> int:
        mob = _count_moves(tm, other)
        s_tm = _sum_w(tm)
        s_ot = _sum_w(other)
        return mob * 30 + (s_tm - s_ot)

    # root ordering: ascending opponent evaluation (lower is better for us)
    scored = []
    for (src, dst) in moves:
        my_new = (my ^ BIT[src]) | BIT[dst]
        ot_new = ot ^ BIT[dst]
        tm2 = ot_new
        ot2 = my_new
        ev = _evaluate(tm2, ot2)
        scored.append((ev, (src, dst)))
    scored.sort(key=lambda x: x[0])
    ordered_root = [m for _, m in scored]
    best_move = ordered_root[0]

    # transposition table: (tm,ot) -> (depth, score, flag, best)
    # flag 0 exact, 1 lower, 2 upper
    TT = {}
    nodes = [0]

    def negamax(tm: int, other: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        nodes[0] += 1
        if (nodes[0] & 1023) == 0:
            _check_timeout()
        key = (tm, other)
        e = TT.get(key)
        tt_move = None
        if e is not None and e[0] >= depth:
            _, s, f, bm = e
            if f == 0:
                return s
            if f == 1 and s >= beta:
                return s
            if f == 2 and s <= alpha:
                return s
            tt_move = bm
        mv = _gen_moves(tm, other)
        if not mv:
            return -MATE + ply
        if depth <= 0:
            return _evaluate(tm, other)
        # order moves: tt move first, then central heuristic
        if tt_move is not None:
            # move to front if present
            try:
                mv.remove(tt_move)
                mv.insert(0, tt_move)
            except ValueError:
                pass
            # sort rest by heuristic but keep tt first
            if len(mv) > 1:
                first = mv[0]
                rest = mv[1:]
                rest.sort(key=lambda x: (2*W[x[1]] - W[x[0]]), reverse=True)
                mv = [first] + rest
        else:
            # cheap central heuristic: keep own central, take opp central
            # higher 2*W[dst]-W[src] better for mover
            mv.sort(key=lambda x: (2*W[x[1]] - W[x[0]]), reverse=True)
        best = -INF
        best_m = mv[0]
        orig_alpha = alpha
        for (src, dst) in mv:
            tm_new = (tm ^ BIT[src]) | BIT[dst]
            ot_new = other ^ BIT[dst]
            # swap
            score = -negamax(ot_new, tm_new, depth-1, -beta, -alpha, ply+1)
            if score > best:
                best = score
                best_m = (src, dst)
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
        # store
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        TT[key] = (depth, best, flag, best_m)
        return best

    try:
        _check_timeout()
        # iterative deepening
        # adapt max depth: total pieces estimate
        max_depth = 30
        for depth in range(1, max_depth+1):
            alpha = -INF
            beta = INF
            cur_best = best_move
            cur_score = -INF
            # search root in current order
            for (src, dst) in ordered_root:
                my_new = (my ^ BIT[src]) | BIT[dst]
                ot_new = ot ^ BIT[dst]
                score = -negamax(ot_new, my_new, depth-1, -beta, -alpha, 1)
                if score > cur_score:
                    cur_score = score
                    cur_best = (src, dst)
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            best_move = cur_best
            # reorder root by last scores? re-evaluate with full window is enough,
            # move best to front for next iteration
            ordered_root.remove(best_move)
            ordered_root.insert(0, best_move)
            # early exit on forced win / loss
            if cur_score >= MATE - 30 or cur_score <= -MATE + 30:
                # if mate in 1, no need deeper; if deeper mate, keep going if time
                if abs(cur_score) >= MATE - 2:
                    break
            # time check for next iteration: if little time left, stop
            if time.perf_counter() > deadline - 0.05:
                break
            # if depth large and branching huge, avoid explosion:
            # estimate: if nodes large, stop
            if nodes[0] > 300000:
                break
    except _Timeout:
        pass
    except Exception:
        pass

    # fallback safety: ensure best_move is legal
    try:
        src, dst = best_move
    except Exception:
        src, dst = moves[0]
    # verify legality, else pick first legal
    legal_set = set(moves)
    if (src, dst) not in legal_set:
        src, dst = moves[0]
    r, c = divmod(src, COLS)
    r2, c2 = divmod(dst, COLS)
    if r2 == r-1:
        d = 'U'
    elif r2 == r+1:
        d = 'D'
    elif c2 == c+1:
        d = 'R'
    elif c2 == c-1:
        d = 'L'
    else:
        # should not happen, fallback to first legal dir search
        for (s, t) in moves:
            if s == src:
                rr, cc = divmod(s, COLS)
                rr2, cc2 = divmod(t, COLS)
                if rr2 == rr-1:
                    d = 'U'
                elif rr2 == rr+1:
                    d = 'D'
                elif cc2 == cc+1:
                    d = 'R'
                else:
                    d = 'L'
                return f'{rr},{cc},{d}'
        return f'{r},{c},U'
    return f'{r},{c},{d}'
