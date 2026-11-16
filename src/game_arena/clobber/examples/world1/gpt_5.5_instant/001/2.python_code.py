
# Clobber 5x6 policy
# Implements: policy(you: list[int], opponent: list[int]) -> str

from functools import lru_cache
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = (
    (-1, 0, "U"),
    (0, 1, "R"),
    (1, 0, "D"),
    (0, -1, "L"),
)

# Precompute neighbors with direction labels
NEI = [[] for _ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, d in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                NEI[i].append((rr * COLS + cc, d))

# Positional preference: mild center/control bias
CENTER_W = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        # higher near center, but kept small versus mobility
        CENTER_W[r * COLS + c] = 6 - (abs(r - 2) + abs(c - 2.5))


def _to_mask(x):
    """Accept either flat length-30 or nested 5x6 lists/arrays."""
    m = 0
    try:
        # flat first
        if len(x) == N and not hasattr(x[0], "__len__"):
            for i, v in enumerate(x):
                if int(v):
                    m |= 1 << i
            return m
    except Exception:
        pass

    k = 0
    for r in range(ROWS):
        row = x[r]
        for c in range(COLS):
            if int(row[c]):
                m |= 1 << k
            k += 1
    return m


def _moves(my, op):
    """Return list of (src, dst, dir)."""
    res = []
    mm = my
    while mm:
        lb = mm & -mm
        s = lb.bit_length() - 1
        for t, d in NEI[s]:
            if (op >> t) & 1:
                res.append((s, t, d))
        mm -= lb
    return res


def _move_count(my, op):
    cnt = 0
    mm = my
    while mm:
        lb = mm & -mm
        s = lb.bit_length() - 1
        for t, _ in NEI[s]:
            cnt += (op >> t) & 1
        mm -= lb
    return cnt


def _apply(my, op, mv):
    s, t, _ = mv
    # our piece moves s -> t, opponent piece at t disappears
    nmy = (my ^ (1 << s)) | (1 << t)
    nop = op ^ (1 << t)
    return nmy, nop


def _static_eval(my, op):
    """
    Evaluation from side-to-move perspective.
    In normal play, having legal moves while opponent has none is decisive.
    Mobility is the dominant heuristic for Clobber.
    """
    mym = _move_count(my, op)
    opm = _move_count(op, my)

    if mym == 0:
        return -100000
    if opm == 0:
        return 100000

    my_pieces = my.bit_count()
    op_pieces = op.bit_count()

    # Frontier/potential contact: pieces adjacent to enemy are useful but can be vulnerable.
    my_center = 0
    op_center = 0
    mm = my
    while mm:
        lb = mm & -mm
        i = lb.bit_length() - 1
        my_center += CENTER_W[i]
        mm -= lb
    oo = op
    while oo:
        lb = oo & -oo
        i = lb.bit_length() - 1
        op_center += CENTER_W[i]
        oo -= lb

    # In Clobber each move removes an opponent stone. Piece count advantage often matters,
    # but mobility/zugzwang matters more.
    return (
        34 * (mym - opm)
        + 9 * (my_pieces - op_pieces)
        + 2 * (my_center - op_center)
    )


def policy(you, opponent) -> str:
    my = _to_mask(you)
    op = _to_mask(opponent)

    legal = _moves(my, op)
    if not legal:
        # Should not be queried in a terminal lost position, but must return a string.
        # Try to return syntactically valid; it may be illegal if no legal move exists.
        return "0,0,R"

    # Deterministic fallback, guaranteed legal if any legal move exists.
    fallback = legal[0]
    best_mv = fallback

    start_time = time.perf_counter()
    limit = 0.92

    # Move ordering: captures that minimize opponent immediate replies first,
    # plus prefer central destination.
    def ordered_moves(a, b):
        ms = _moves(a, b)
        scored = []
        for mv in ms:
            na, nb = _apply(a, b, mv)
            # after our move, opponent is side-to-move with masks (nb, na)
            opp_replies = _move_count(nb, na)
            dst = mv[1]
            score = -opp_replies * 20 + CENTER_W[dst]
            scored.append((score, mv))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [m for _, m in scored]

    # Transposition table per call
    tt = {}

    def negamax(a, b, depth, alpha, beta):
        # a = side-to-move stones, b = opponent stones
        if time.perf_counter() - start_time > limit:
            raise TimeoutError

        key = (a, b, depth)
        val = tt.get(key)
        if val is not None:
            return val

        ms = ordered_moves(a, b)
        if not ms:
            return -100000 - depth  # losing sooner is worse

        if depth <= 0:
            return _static_eval(a, b)

        best = -10**9
        for mv in ms:
            na, nb = _apply(a, b, mv)
            # turn swaps: opponent's stones become side-to-move
            score = -negamax(nb, na, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    # Iterative deepening. Branching is usually modest on 5x6.
    max_depth = 7
    try:
        for depth in range(1, max_depth + 1):
            current_best = best_mv
            current_score = -10**9

            for mv in ordered_moves(my, op):
                na, nb = _apply(my, op, mv)
                score = -negamax(nb, na, depth - 1, -10**9, 10**9)

                # Immediate winning response is excellent
                if score > current_score:
                    current_score = score
                    current_best = mv

            best_mv = current_best

            # If we found a forced win in this horizon, no need to spend more.
            if current_score > 90000:
                break

    except TimeoutError:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        best_mv = fallback

    s, t, d = best_mv
    r, c = divmod(s, COLS)
    return f"{r},{c},{d}"
