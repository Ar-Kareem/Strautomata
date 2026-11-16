
import time
import math
import random

ROWS = 5
COLS = 6
DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

# Deterministic mild preference for central squares.
CENTER_W = (
    (1, 2, 3, 3, 2, 1),
    (2, 4, 5, 5, 4, 2),
    (3, 5, 7, 7, 5, 3),
    (2, 4, 5, 5, 4, 2),
    (1, 2, 3, 3, 2, 1),
)

def _flat_to_bits(arr):
    """Convert 30-entry list-like or 5x6 nested/list/numpy array to bitboard."""
    b = 0
    k = 0
    try:
        # Works for flat Python lists and numpy arrays often enough.
        if len(arr) == 30 and not hasattr(arr[0], "__len__"):
            for i, v in enumerate(arr):
                if v:
                    b |= (1 << i)
            return b
    except Exception:
        pass

    for r in range(ROWS):
        for c in range(COLS):
            try:
                v = arr[r][c]
            except Exception:
                v = arr[k]
            if v:
                b |= (1 << k)
            k += 1
    return b

def _moves(me, opp):
    """Return legal moves as tuples: (from_index, to_index, dir_char)."""
    res = []
    for i in range(30):
        if (me >> i) & 1:
            r = i // COLS
            c = i - r * COLS
            if r > 0:
                j = i - COLS
                if (opp >> j) & 1:
                    res.append((i, j, "U"))
            if c < COLS - 1:
                j = i + 1
                if (opp >> j) & 1:
                    res.append((i, j, "R"))
            if r < ROWS - 1:
                j = i + COLS
                if (opp >> j) & 1:
                    res.append((i, j, "D"))
            if c > 0:
                j = i - 1
                if (opp >> j) & 1:
                    res.append((i, j, "L"))
    return res

def _apply(me, opp, mv):
    """Apply move for side me; return next state from opponent perspective."""
    frm, to, _ = mv
    me2 = (me & ~(1 << frm)) | (1 << to)
    opp2 = opp & ~(1 << to)
    # Next player sees their stones as me.
    return opp2, me2

def _popcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _mobility_count(me, opp):
    cnt = 0
    for i in range(30):
        if (me >> i) & 1:
            r = i // COLS
            c = i - r * COLS
            if r > 0 and ((opp >> (i - COLS)) & 1): cnt += 1
            if c < COLS - 1 and ((opp >> (i + 1)) & 1): cnt += 1
            if r < ROWS - 1 and ((opp >> (i + COLS)) & 1): cnt += 1
            if c > 0 and ((opp >> (i - 1)) & 1): cnt += 1
    return cnt

def _center_score(bits):
    s = 0
    for i in range(30):
        if (bits >> i) & 1:
            s += CENTER_W[i // COLS][i % COLS]
    return s

def _adj_same(bits):
    """Small cohesion score: adjacent friendly pairs."""
    s = 0
    for r in range(ROWS):
        base = r * COLS
        for c in range(COLS):
            i = base + c
            if (bits >> i) & 1:
                if c < COLS - 1 and ((bits >> (i + 1)) & 1): s += 1
                if r < ROWS - 1 and ((bits >> (i + COLS)) & 1): s += 1
    return s

def _evaluate(me, opp):
    mym = _mobility_count(me, opp)
    opm = _mobility_count(opp, me)

    if mym == 0:
        return -1000000
    if opm == 0:
        return 1000000

    # In Clobber, having fewer pieces can be good, but mobility dominates.
    myp = _popcount(me)
    oppp = _popcount(opp)

    score = 0
    score += 120 * (mym - opm)
    score += 18 * (oppp - myp)       # prefer having captured more / fewer own liabilities
    score += 4 * (_center_score(me) - _center_score(opp))
    score += 7 * (_adj_same(me) - _adj_same(opp))

    # Penalize being capturable many ways next turn; this is partly opm already,
    # but kept small to shape quiet positions.
    score -= 10 * opm
    return score

def _move_order_key(me, opp, mv):
    frm, to, d = mv
    me2 = (me & ~(1 << frm)) | (1 << to)
    opp2 = opp & ~(1 << to)
    # Good if opponent has few replies after this move; central destination helps.
    replies = _mobility_count(opp2, me2)
    r = to // COLS
    c = to % COLS
    return (replies, -CENTER_W[r][c])

def policy(you, opponent):
    start_time = time.perf_counter()
    deadline = start_time + 0.92

    me = _flat_to_bits(you)
    opp = _flat_to_bits(opponent)

    legal = _moves(me, opp)
    if not legal:
        # Problem statement should not ask for a move in terminal states.
        # Still return a syntactically valid-looking fallback; no legal move exists.
        return "0,0,U"

    # Deterministic fallback: move that minimizes opponent immediate mobility.
    legal.sort(key=lambda m: _move_order_key(me, opp, m))
    best_move = legal[0]

    tt = {}

    def negamax(meb, oppb, depth, alpha, beta):
        if time.perf_counter() >= deadline:
            raise TimeoutError

        key = (meb, oppb, depth)
        old = tt.get(key)
        if old is not None:
            return old

        ms = _moves(meb, oppb)
        if not ms:
            return -1000000 - depth  # losing sooner is worse

        if depth <= 0:
            val = _evaluate(meb, oppb)
            tt[key] = val
            return val

        ms.sort(key=lambda m: _move_order_key(meb, oppb, m))
        best = -10**9

        for mv in ms:
            nme, nopp = _apply(meb, oppb, mv)
            val = -negamax(nme, nopp, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    # Iterative deepening. Branching is usually moderate on 5x6.
    max_depth = 10
    depth = 1
    while depth <= max_depth:
        try:
            alpha = -10**9
            beta = 10**9
            current_best = best_move
            current_score = -10**9

            ordered = list(legal)
            ordered.sort(key=lambda m: (m != best_move, _move_order_key(me, opp, m)))

            for mv in ordered:
                if time.perf_counter() >= deadline:
                    raise TimeoutError
                nme, nopp = _apply(me, opp, mv)
                score = -negamax(nme, nopp, depth - 1, -beta, -alpha)

                # Tiny deterministic tie-breaker: prefer central captures and stable order.
                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best

            # Found forced win; no need to spend time.
            if current_score > 900000:
                break

            depth += 1
        except TimeoutError:
            break
        except Exception:
            # Never risk failing to return a legal move.
            break

    frm, to, d = best_move
    return str(frm // COLS) + "," + str(frm % COLS) + "," + d
