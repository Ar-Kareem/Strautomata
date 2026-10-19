
# Clobber 5x6 policy
# Required API:
#   def policy(you: list[int], opponent: list[int]) -> str

import time
from functools import lru_cache

ROWS, COLS = 5, 6
N = ROWS * COLS
DIRS = ((-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L'))

# Bit for each square
BITS = [1 << i for i in range(N)]

# Precomputed directed adjacent moves: (from_index, to_index, dir_char)
ADJ = []
ADJ_FROM = [[] for _ in range(N)]
NEI_MASK = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                ADJ.append((i, j, ch))
                ADJ_FROM[i].append((j, ch))
                NEI_MASK[i] |= BITS[j]

# Center preference: useful as a small tie-breaker
CENTER_SCORE = []
for r in range(ROWS):
    for c in range(COLS):
        # Higher is more central
        CENTER_SCORE.append(10 - (abs(r - 2) + abs(c - 2.5)))


def _to_bits(arr):
    """Convert flat/nested/list/numpy-like 5x6 input to bitboard."""
    b = 0
    k = 0
    # Common case: nested 5x6
    try:
        if len(arr) == ROWS and hasattr(arr[0], "__len__"):
            for r in range(ROWS):
                row = arr[r]
                for c in range(COLS):
                    if row[c]:
                        b |= BITS[k]
                    k += 1
            return b
    except Exception:
        pass

    # Flat list or numpy array flattened by indexing
    try:
        for i in range(N):
            if arr[i]:
                b |= BITS[i]
        return b
    except Exception:
        # Very defensive fallback
        flat = list(arr)
        for i, v in enumerate(flat[:N]):
            if v:
                b |= BITS[i]
        return b


def _moves(my, op):
    """Return legal moves as tuples (from, to, dir)."""
    res = []
    m = my
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        targets = NEI_MASK[i] & op
        t = targets
        while t:
            tb = t & -t
            j = tb.bit_length() - 1
            # determine direction
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
            t -= tb
        m -= lsb
    return res


def _move_count(my, op):
    cnt = 0
    m = my
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        cnt += (NEI_MASK[i] & op).bit_count()
        m -= lsb
    return cnt


def _piece_count(x):
    return x.bit_count()


def _frontier_count(my, op):
    """Number of pieces that have at least one capture."""
    cnt = 0
    m = my
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        if NEI_MASK[i] & op:
            cnt += 1
        m -= lsb
    return cnt


def _center_sum(my):
    s = 0.0
    m = my
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        s += CENTER_SCORE[i]
        m -= lsb
    return s


def _apply(my, op, mv):
    """Apply my move and return board from opponent's perspective: (new_opp_to_move, new_me_waiting)."""
    i, j, _ = mv
    bi, bj = BITS[i], BITS[j]
    new_my = (my & ~bi) | bj
    new_op = op & ~bj
    return new_op, new_my


def _static_eval(my, op):
    """
    Evaluation from side-to-move perspective.
    In normal play, no move is losing/winning, handled by search.
    """
    my_mob = _move_count(my, op)
    op_mob = _move_count(op, my)

    my_front = _frontier_count(my, op)
    op_front = _frontier_count(op, my)

    # Having fewer pieces can be good in Clobber, but mobility dominates.
    # Slightly prefer limiting opponent pieces and options.
    pc_diff = _piece_count(my) - _piece_count(op)
    cen = _center_sum(my) - _center_sum(op)

    return 100 * (my_mob - op_mob) + 18 * (my_front - op_front) - 4 * pc_diff + 0.5 * cen


def _ordered_moves(my, op):
    ms = _moves(my, op)

    def score(mv):
        i, j, _ = mv
        n_op, n_my = _apply(my, op, mv)  # opponent to move
        opp_replies = _move_count(n_op, n_my)
        my_next = _move_count(n_my, n_op)
        # Prefer moves that leave opponent with few replies, keep us active, and land centrally.
        return -80 * opp_replies + 20 * my_next + CENTER_SCORE[j] - 0.1 * CENTER_SCORE[i]

    ms.sort(key=score, reverse=True)
    return ms


def policy(you, opponent) -> str:
    start_time = time.perf_counter()
    time_limit = 0.90

    my = _to_bits(you)
    op = _to_bits(opponent)

    legal = _ordered_moves(my, op)
    if not legal:
        # No legal move exists. The game should not request a move here, but return a well-formed string.
        return "0,0,U"

    # Immediate winning move: leaves opponent no legal moves.
    for mv in legal:
        n_op, n_my = _apply(my, op, mv)
        if _move_count(n_op, n_my) == 0:
            i, j, ch = mv
            return f"{i // COLS},{i % COLS},{ch}"

    best_move = legal[0]

    # Transposition table is local per call to avoid stale growth.
    tt = {}

    def negamax(myb, opb, depth, alpha, beta):
        # Time guard
        if time.perf_counter() - start_time > time_limit:
            raise TimeoutError

        key = (myb, opb, depth)
        if key in tt:
            return tt[key]

        ms = _ordered_moves(myb, opb)
        if not ms:
            # Side to move loses.
            return -1000000 - depth

        if depth <= 0:
            return _static_eval(myb, opb)

        best = -10**9
        a0 = alpha

        for mv in ms:
            nb_op, nb_my = _apply(myb, opb, mv)
            val = -negamax(nb_op, nb_my, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    # Iterative deepening. On 30 squares this is usually enough and safe under 1s.
    max_depth = 8
    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start_time > time_limit:
                break

            current_best = best_move
            current_score = -10**9
            alpha = -10**9
            beta = 10**9

            # Reorder with previous best first
            root_moves = legal[:]
            if best_move in root_moves:
                root_moves.remove(best_move)
                root_moves.insert(0, best_move)

            for mv in root_moves:
                if time.perf_counter() - start_time > time_limit:
                    raise TimeoutError

                n_op, n_my = _apply(my, op, mv)
                val = -negamax(n_op, n_my, depth - 1, -beta, -alpha)

                if val > current_score:
                    current_score = val
                    current_best = mv
                if val > alpha:
                    alpha = val

            best_move = current_best

            # Found forced win; no need to search deeper.
            if current_score > 900000:
                break

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: retain legal fallback.
        best_move = legal[0]

    i, j, ch = best_move
    return f"{i // COLS},{i % COLS},{ch}"
