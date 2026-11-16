
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]
INF = 10 ** 9
MATE = 10 ** 7


def _flatten(board):
    if hasattr(board, "flatten"):
        return list(board.flatten())
    if len(board) == ROWS and hasattr(board[0], "__iter__"):
        out = []
        for r in range(ROWS):
            for c in range(COLS):
                out.append(board[r][c])
        return out
    return list(board)


def _to_bits(board):
    arr = _flatten(board)
    bits = 0
    for i, v in enumerate(arr[:N]):
        if v:
            bits |= 1 << i
    return bits


def _idx(r, c):
    return r * COLS + c


def _rc(i):
    return divmod(i, COLS)


def _bitcount(x):
    return x.bit_count()


def _legal_moves(you, opp):
    moves = []
    b = you
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        r, c = _rc(s)
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                d = _idx(nr, nc)
                if (opp >> d) & 1:
                    moves.append((s, d, ch))
        b ^= lsb
    return moves


def _move_to_str(m):
    s, d, ch = m
    r, c = _rc(s)
    return f"{r},{c},{ch}"


def _apply(you, opp, move):
    s, d, _ = move
    you2 = (you & ~(1 << s)) | (1 << d)
    opp2 = opp & ~(1 << d)
    return you2, opp2


def _mobility(you, opp):
    cnt = 0
    b = you
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        r, c = _rc(s)
        if r > 0 and ((opp >> (s - COLS)) & 1):
            cnt += 1
        if r < ROWS - 1 and ((opp >> (s + COLS)) & 1):
            cnt += 1
        if c > 0 and ((opp >> (s - 1)) & 1):
            cnt += 1
        if c < COLS - 1 and ((opp >> (s + 1)) & 1):
            cnt += 1
        b ^= lsb
    return cnt


def _frontier_score(you, opp):
    score = 0
    b = you
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        r, c = _rc(s)
        adj_empty = 0
        adj_opp = 0
        for dr, dc, _ in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                t = _idx(nr, nc)
                if (opp >> t) & 1:
                    adj_opp += 1
                elif not ((you >> t) & 1):
                    adj_empty += 1
        score += 2 * adj_opp + adj_empty
        b ^= lsb
    return score


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    deadline = start_time + 0.92

    me = _to_bits(you)
    op = _to_bits(opponent)

    root_moves = _legal_moves(me, op)

    if not root_moves:
        # This should not be requested by the arena on a live turn.
        # Return a syntactically valid placeholder; no legal move exists.
        return "0,0,R"

    fallback = root_moves[0]
    best_move = fallback

    # Immediate win check.
    scored_root = []
    for m in root_moves:
        me2, op2 = _apply(me, op, m)
        opp_replies = _mobility(op2, me2)
        if opp_replies == 0:
            return _move_to_str(m)
        my_future = _mobility(me2, op2)
        # Prefer moves that reduce opponent mobility while preserving ours.
        h = 12 * opp_replies - 5 * my_future + _bitcount(op2)
        scored_root.append((h, m))
    scored_root.sort(key=lambda x: x[0])
    root_moves = [m for _, m in scored_root]
    best_move = root_moves[0]

    nodes = [0]
    tt = {}

    def timed_out():
        return time.perf_counter() >= deadline

    def evaluate(a, b):
        ma = _mobility(a, b)
        if ma == 0:
            return -MATE
        mb = _mobility(b, a)
        if mb == 0:
            return MATE - 1

        pa = _bitcount(a)
        pb = _bitcount(b)

        fa = _frontier_score(a, b)
        fb = _frontier_score(b, a)

        # In Clobber, having many moves is usually good, but forcing the
        # opponent into low mobility is even more important.
        return (
            120 * (ma - mb)
            + 18 * (fa - fb)
            + 7 * (pa - pb)
        )

    def ordered_moves(a, b):
        ms = _legal_moves(a, b)
        vals = []
        for m in ms:
            a2, b2 = _apply(a, b, m)
            opp_mob = _mobility(b2, a2)
            if opp_mob == 0:
                vals.append((-1000000, m))
            else:
                own_mob = _mobility(a2, b2)
                vals.append((20 * opp_mob - 7 * own_mob, m))
        vals.sort(key=lambda x: x[0])
        return [m for _, m in vals]

    def negamax(a, b, depth, alpha, beta, ply):
        nodes[0] += 1
        if (nodes[0] & 511) == 0 and timed_out():
            raise TimeoutError

        moves = _legal_moves(a, b)
        if not moves:
            return -MATE + ply

        if depth <= 0:
            return evaluate(a, b)

        key = (a, b, depth)
        if key in tt:
            return tt[key]

        best = -INF

        vals = []
        for m in moves:
            a2, b2 = _apply(a, b, m)
            om = _mobility(b2, a2)
            if om == 0:
                vals.append((-1000000, m))
            else:
                vals.append((20 * om - 7 * _mobility(a2, b2), m))
        vals.sort(key=lambda x: x[0])

        for _, m in vals:
            a2, b2 = _apply(a, b, m)
            score = -negamax(b2, a2, depth - 1, -beta, -alpha, ply + 1)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    depth = 1
    while depth <= 30:
        if timed_out():
            break

        current_best = best_move
        current_score = -INF

        try:
            # Principal variation move first from previous completed depth.
            ordered = root_moves[:]
            if best_move in ordered:
                ordered.remove(best_move)
                ordered.insert(0, best_move)

            alpha = -INF
            beta = INF

            for m in ordered:
                if timed_out():
                    raise TimeoutError

                me2, op2 = _apply(me, op, m)
                score = -negamax(op2, me2, depth - 1, -beta, -alpha, 1)

                if score > current_score:
                    current_score = score
                    current_best = m

                if score > alpha:
                    alpha = score

            best_move = current_best

            # If a forced win is found, no need to search much deeper.
            if current_score > MATE // 2:
                break

            depth += 1

        except TimeoutError:
            break
        except Exception:
            # Safety net: never risk failing to return a legal move.
            break

    return _move_to_str(best_move)
