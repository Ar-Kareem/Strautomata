
# Clobber 5x6 policy
# API: policy(you: list[int], opponent: list[int]) -> str

import time
import math
from functools import lru_cache

ROWS, COLS = 5, 6
N = ROWS * COLS
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precompute neighbor masks and directed move data
NEI = [[] for _ in range(N)]
MOVE_DATA = []
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEI[i].append(j)
                MOVE_DATA.append((i, j, ch))

CENTER_WEIGHT = [
    1, 2, 2, 2, 2, 1,
    2, 3, 3, 3, 3, 2,
    2, 3, 4, 4, 3, 2,
    2, 3, 3, 3, 3, 2,
    1, 2, 2, 2, 2, 1,
]

# Zobrist-like deterministic bit mixing for transposition keys is unnecessary:
# the bitboards themselves form compact exact keys.


def _to_bits(arr):
    """Convert flat or nested 5x6 0/1 list/array to bitboard."""
    b = 0
    k = 0
    try:
        # Handles nested lists / numpy arrays shaped (5,6)
        if len(arr) == ROWS and hasattr(arr[0], "__len__"):
            for r in range(ROWS):
                row = arr[r]
                for c in range(COLS):
                    if int(row[c]):
                        b |= 1 << (r * COLS + c)
            return b
    except Exception:
        pass

    # Handles flat list / numpy array length 30
    for x in arr:
        if int(x):
            b |= 1 << k
        k += 1
        if k >= N:
            break
    return b


def _bitcount(x):
    return x.bit_count()


def _moves(me, opp):
    """Return legal moves as tuples (from, to, dirchar)."""
    res = []
    m = me
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        for j in NEI[i]:
            if (opp >> j) & 1:
                # compute direction char
                d = j - i
                if d == -COLS:
                    ch = 'U'
                elif d == COLS:
                    ch = 'D'
                elif d == 1:
                    ch = 'R'
                else:
                    ch = 'L'
                res.append((i, j, ch))
        m -= lsb
    return res


def _mobility(me, opp):
    cnt = 0
    m = me
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        for j in NEI[i]:
            cnt += (opp >> j) & 1
        m -= lsb
    return cnt


def _apply(me, opp, mv):
    i, j, _ = mv
    # our piece moves i -> j and captures opp at j.
    nme = (me & ~(1 << i)) | (1 << j)
    nopp = opp & ~(1 << j)
    # Return from opponent's perspective: opponent to move becomes "me".
    return nopp, nme


def _move_to_str(mv):
    i, _, ch = mv
    return f"{i // COLS},{i % COLS},{ch}"


def _center_score(bits):
    s = 0
    b = bits
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        s += CENTER_WEIGHT[i]
        b -= lsb
    return s


def _exposure_score(me, opp):
    """
    Counts pieces exposed to captures and defended captures.
    Positive means good for side 'me'.
    """
    my_exposed = 0
    opp_exposed = 0
    my_frontier = 0
    opp_frontier = 0

    b = me
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        adj_opp = 0
        for j in NEI[i]:
            if (opp >> j) & 1:
                adj_opp += 1
        if adj_opp:
            my_exposed += 1
            my_frontier += adj_opp
        b -= lsb

    b = opp
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        adj_me = 0
        for j in NEI[i]:
            if (me >> j) & 1:
                adj_me += 1
        if adj_me:
            opp_exposed += 1
            opp_frontier += adj_me
        b -= lsb

    return 3 * (opp_exposed - my_exposed) + (opp_frontier - my_frontier)


def _static_eval(me, opp):
    """
    Evaluation from side-to-move 'me'.
    In normal play Clobber, mobility is crucial; no move is immediate loss.
    """
    mymob = _mobility(me, opp)
    oppmob = _mobility(opp, me)

    if mymob == 0:
        return -100000
    if oppmob == 0:
        return 100000

    material = _bitcount(me) - _bitcount(opp)
    center = _center_score(me) - _center_score(opp)
    exposure = _exposure_score(me, opp)

    # Prefer having options while restricting opponent. Material is secondary:
    # captures are mandatory only indirectly, and fewer pieces can sometimes help.
    return 120 * (mymob - oppmob) + 18 * material + 3 * center + 7 * exposure


def _ordered_moves(me, opp):
    ms = _moves(me, opp)
    scored = []
    for mv in ms:
        nme, nopp = _apply(me, opp, mv)
        # nme/nopp are already opponent perspective; score after move for us is negative eval.
        immediate = -_static_eval(nme, nopp)
        i, j, _ = mv
        # Bonus if captured piece was highly connected; slight center preference.
        conn = 0
        for k in NEI[j]:
            if (me >> k) & 1:
                conn += 1
        scored.append((immediate + 4 * conn + CENTER_WEIGHT[j], mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def policy(you: list[int], opponent: list[int]) -> str:
    start = time.perf_counter()
    limit = 0.92  # keep margin under 1s

    me = _to_bits(you)
    opp = _to_bits(opponent)

    legal = _moves(me, opp)
    if not legal:
        # No legal move exists. The arena should not request a move in lost states,
        # but return a syntactically valid-looking fallback to avoid crashing.
        return "0,0,R"

    best_move = legal[0]
    if len(legal) == 1:
        return _move_to_str(best_move)

    tt = {}

    def timed_out():
        return time.perf_counter() - start > limit

    def negamax(me_b, opp_b, depth, alpha, beta):
        if timed_out():
            raise TimeoutError

        key = (me_b, opp_b, depth)
        val = tt.get(key)
        if val is not None:
            return val

        ms = _ordered_moves(me_b, opp_b)
        if not ms:
            return -100000 - depth  # losing sooner is worse

        if depth == 0:
            return _static_eval(me_b, opp_b)

        best = -10**9
        a0 = alpha

        for mv in ms:
            cme, copp = _apply(me_b, opp_b, mv)
            score = -negamax(cme, copp, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        # Store exact-ish value; simple and safe enough for this small search.
        if best <= a0 or best >= beta:
            # still useful as a bound-like ordering value, but exact depth key avoids harm mostly
            pass
        tt[key] = best
        return best

    # Check immediate winning moves first.
    for mv in _ordered_moves(me, opp):
        nme, nopp = _apply(me, opp, mv)
        if _mobility(nme, nopp) == 0:  # opponent to move has no legal moves
            return _move_to_str(mv)

    # Iterative deepening. 5x6 Clobber usually has modest branching after openings.
    max_depth = 9
    try:
        for depth in range(1, max_depth + 1):
            alpha = -10**9
            beta = 10**9
            local_best = best_move
            local_score = -10**9

            for mv in _ordered_moves(me, opp):
                if timed_out():
                    raise TimeoutError
                nme, nopp = _apply(me, opp, mv)
                score = -negamax(nme, nopp, depth - 1, -beta, -alpha)
                if score > local_score:
                    local_score = score
                    local_best = mv
                if score > alpha:
                    alpha = score

            best_move = local_best

            # If a forced win/loss is clearly found, no need to search deeper.
            if local_score > 90000:
                break

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: always return a legal move.
        return _move_to_str(best_move)

    return _move_to_str(best_move)
