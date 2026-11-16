
import time

ROWS, COLS = 5, 6
N = ROWS * COLS
FULL = (1 << N) - 1
COL0 = sum(1 << (r * COLS) for r in range(ROWS))
COL5 = sum(1 << (r * COLS + COLS - 1) for r in range(ROWS))
NOT_COL0 = FULL & ~COL0
NOT_COL5 = FULL & ~COL5

WIN = 100000
TIME_LIMIT = 0.75

try:
    (1).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')


class Timeout(Exception):
    pass


_tt = {}
_deadline = 0.0
_nodes = 0


def gen_moves(P, O):
    moves = []
    up = (P >> 6) & O
    down = (P << 6) & O
    left = ((P & NOT_COL0) >> 1) & O
    right = ((P & NOT_COL5) << 1) & O
    for bits, delta, d in ((up, 6, 'U'), (down, -6, 'D'), (left, 1, 'L'), (right, -1, 'R')):
        while bits:
            lsb = bits & -bits
            to = lsb.bit_length() - 1
            moves.append((to + delta, to, d))
            bits ^= lsb
    return moves


def mobility(P, O):
    return (popcount((P >> 6) & O) + popcount((P << 6) & O) +
            popcount(((P & NOT_COL0) >> 1) & O) + popcount(((P & NOT_COL5) << 1) & O))


def active_pieces(P, O):
    # pieces of P adjacent to at least one O piece
    adj = (O << 6) | (O >> 6) | ((O & NOT_COL0) >> 1) | ((O & NOT_COL5) << 1)
    return popcount(P & adj & FULL)


def evaluate(P, O):
    # from perspective of player P (to move)
    return 4 * (mobility(P, O) - mobility(O, P)) + (active_pieces(P, O) - active_pieces(O, P))


def negamax(P, O, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() > _deadline:
        raise Timeout()

    key = (P, O)
    entry = _tt.get(key)
    tt_move = None
    if entry is not None:
        e_depth, e_flag, e_val, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag == 1:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves = gen_moves(P, O)
    if not moves:
        return -(WIN + depth)
    if depth <= 0:
        return evaluate(P, O)

    # move ordering
    scored = []
    for m in moves:
        fr, to, d = m
        nP = P ^ (1 << fr) ^ (1 << to)
        nO = O ^ (1 << to)
        if m == tt_move:
            s = 10 ** 6
        elif depth >= 2:
            s = -evaluate(nO, nP)
        else:
            s = 0
        scored.append((s, m, nP, nO))
    scored.sort(key=lambda x: -x[0])

    best_val = -10 ** 9
    best_move = None
    orig_alpha = alpha
    for s, m, nP, nO in scored:
        val = -negamax(nO, nP, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best_val <= orig_alpha:
        flag = 2
    elif best_val >= beta:
        flag = 1
    else:
        flag = 0
    _tt[key] = (depth, flag, best_val, best_move)
    return best_val


def to_str(m):
    fr, to, d = m
    return "%d,%d,%s" % (fr // COLS, fr % COLS, d)


def policy(you, opponent):
    global _deadline, _nodes, _tt
    start = time.time()
    _deadline = start + TIME_LIMIT

    P = 0
    O = 0
    for r in range(ROWS):
        yr = you[r]
        orow = opponent[r]
        for c in range(COLS):
            if yr[c]:
                P |= 1 << (r * COLS + c)
            elif orow[c]:
                O |= 1 << (r * COLS + c)

    moves = gen_moves(P, O)
    if not moves:
        # No legal move exists; return something syntactically valid.
        return "0,0,R"
    if len(moves) == 1:
        return to_str(moves[0])

    if len(_tt) > 1500000:
        _tt = {}

    # Fallback: best by 1-ply static evaluation
    best_move = None
    best_s = -10 ** 9
    for m in moves:
        fr, to, d = m
        nP = P ^ (1 << fr) ^ (1 << to)
        nO = O ^ (1 << to)
        s = -evaluate(nO, nP)
        if s > best_s:
            best_s = s
            best_move = m

    depth = 1
    _nodes = 0
    try:
        while depth <= 60:
            # root search
            ordered = []
            entry = _tt.get((P, O))
            tt_move = entry[3] if entry is not None else None
            for m in moves:
                fr, to, d = m
                nP = P ^ (1 << fr) ^ (1 << to)
                nO = O ^ (1 << to)
                if m == best_move:
                    s = 10 ** 7
                elif m == tt_move:
                    s = 10 ** 6
                else:
                    s = -evaluate(nO, nP)
                ordered.append((s, m, nP, nO))
            ordered.sort(key=lambda x: -x[0])

            alpha = -10 ** 9
            beta = 10 ** 9
            cur_best = None
            cur_val = -10 ** 9
            for s, m, nP, nO in ordered:
                val = -negamax(nO, nP, depth - 1, -beta, -alpha)
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
                _tt[(P, O)] = (depth, 0, cur_val, cur_best)
            if cur_val >= WIN or cur_val <= -WIN:
                break
            depth += 1
    except Timeout:
        pass

    return to_str(best_move)
