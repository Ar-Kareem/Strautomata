
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
INF = 10**9
WIN = 10**6

# ---------------------------------------------------------------------
# Board precomputation
# ---------------------------------------------------------------------

_NEI = [0] * N
_DEG = [0] * N
_MOVE_STR = [""] * (N * N)

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for ch, dr, dc in (("U", -1, 0), ("R", 0, 1), ("D", 1, 0), ("L", 0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                _NEI[i] |= 1 << j
                _MOVE_STR[i * N + j] = f"{r},{c},{ch}"
        _DEG[i] = _NEI[i].bit_count()

# Fast adjacency and degree sums by 15-bit halves.
_LOW15 = (1 << 15) - 1
_SIZE15 = 1 << 15
_ADJ0 = [0] * _SIZE15
_ADJ1 = [0] * _SIZE15
_DSUM0 = [0] * _SIZE15
_DSUM1 = [0] * _SIZE15

for m in range(1, _SIZE15):
    b = m & -m
    k = b.bit_length() - 1
    p = m ^ b
    _ADJ0[m] = _ADJ0[p] | _NEI[k]
    _ADJ1[m] = _ADJ1[p] | _NEI[15 + k]
    _DSUM0[m] = _DSUM0[p] + _DEG[k]
    _DSUM1[m] = _DSUM1[p] + _DEG[15 + k]


_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


# ---------------------------------------------------------------------
# Bitboard utilities
# ---------------------------------------------------------------------

def _to_mask(arr) -> int:
    """Accepts either a flat length-30 array/list or a 5x6 nested array/list."""
    m = 0
    try:
        nested = (len(arr) == ROWS and len(arr[0]) == COLS)
    except Exception:
        nested = False

    if nested:
        for r in range(ROWS):
            row = arr[r]
            base = r * COLS
            for c in range(COLS):
                if row[c]:
                    m |= 1 << (base + c)
    else:
        for i in range(N):
            if arr[i]:
                m |= 1 << i
    return m


def _adj_mask(m: int) -> int:
    return _ADJ0[m & _LOW15] | _ADJ1[(m >> 15) & _LOW15]


def _deg_sum(m: int) -> int:
    return _DSUM0[m & _LOW15] + _DSUM1[(m >> 15) & _LOW15]


def _has_moves(c: int, o: int) -> bool:
    return (_adj_mask(c) & o) != 0


def _edge_count(c: int, o: int) -> int:
    """Number of legal moves/contact edges for side c against side o."""
    x = c & _adj_mask(o)
    cnt = 0
    while x:
        b = x & -x
        i = b.bit_length() - 1
        cnt += (_NEI[i] & o).bit_count()
        x ^= b
    return cnt


def _gen_moves(c: int, o: int):
    moves = []
    active = c & _adj_mask(o)
    while active:
        fb = active & -active
        f = fb.bit_length() - 1
        y = _NEI[f] & o
        while y:
            tb = y & -y
            t = tb.bit_length() - 1
            moves.append(f * N + t)
            y ^= tb
        active ^= fb
    return moves


def _apply(c: int, o: int, mv: int):
    f = mv // N
    t = mv - f * N
    fb = 1 << f
    tb = 1 << t

    # After making our move, roles swap:
    # next current side is old opponent without the captured target.
    # next opponent side is our old side, moved from f to t.
    return o ^ tb, (c ^ fb) | tb


def _immediate_win_exists(c: int, o: int) -> bool:
    """True if side c has a move leaving the opponent with no legal move."""
    active = c & _adj_mask(o)
    while active:
        fb = active & -active
        f = fb.bit_length() - 1
        y = _NEI[f] & o
        while y:
            tb = y & -y
            c2 = o ^ tb
            o2 = (c ^ fb) | tb
            if (_adj_mask(c2) & o2) == 0:
                return True
            y ^= tb
        active ^= fb
    return False


# ---------------------------------------------------------------------
# Evaluation and move ordering
# ---------------------------------------------------------------------

def _quick_eval_edges(c: int, o: int, edges: int) -> int:
    """
    Heuristic from the viewpoint of side c to move.
    Active opponent pieces are good targets; active own pieces are pieces
    we may be forced to sacrifice. Material matters, but tactics dominate.
    """
    adj_c = _adj_mask(c)
    adj_o = _adj_mask(o)

    active_c_mask = c & adj_o
    active_o_mask = o & adj_c

    pc = c.bit_count()
    po = o.bit_count()
    ac = active_c_mask.bit_count()
    ao = active_o_mask.bit_count()

    safe_c = pc - ac
    safe_o = po - ao

    score = 35 * (pc - po)
    score += 60 * (ao - ac)
    score += 10 * (safe_c - safe_o)
    score += 6 * (_deg_sum(active_o_mask) - _deg_sum(active_c_mask))

    # Low-contact positions often contain immediate tactical wins for the
    # player to move; zero-contact is terminal and handled elsewhere.
    if edges <= 12:
        score += (13 - edges) * 10
    else:
        score -= edges

    return score


def _static_eval(c: int, o: int) -> int:
    edges = _edge_count(c, o)
    if edges == 0:
        return -WIN

    # At quiet horizons, still notice small immediate wins.
    if edges <= 7 and _immediate_win_exists(c, o):
        return WIN // 2

    return _quick_eval_edges(c, o, edges)


def _ordered_moves(c: int, o: int, preferred: int = -1):
    scored = []
    active = c & _adj_mask(o)

    while active:
        fb = active & -active
        f = fb.bit_length() - 1
        y = _NEI[f] & o

        while y:
            tb = y & -y
            t = tb.bit_length() - 1
            mv = f * N + t

            if mv == preferred:
                s = 10**9
            else:
                c2 = o ^ tb
                o2 = (c ^ fb) | tb

                # Best tactical move: leave opponent with no legal move.
                if (_adj_mask(c2) & o2) == 0:
                    s = 800000 + _DEG[f] + _DEG[t]
                else:
                    e2 = _edge_count(c2, o2)
                    s = -_quick_eval_edges(c2, o2, e2)

                    # Avoid handing the opponent an immediate finish.
                    if e2 <= 7 and _immediate_win_exists(c2, o2):
                        s -= 250000

                    # Prefer moves that reduce future contact.
                    s -= 8 * e2
                    s += 3 * (_DEG[f] + _DEG[t])

                    # Tiny deterministic tie-breaker.
                    s += ((mv * 37 + c + (o >> 3)) & 7)

            scored.append((s, mv))
            y ^= tb

        active ^= fb

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def _heuristic_root_move(c: int, o: int, moves):
    best = moves[0]
    best_score = -INF

    for mv in moves:
        c2, o2 = _apply(c, o, mv)

        if not _has_moves(c2, o2):
            return mv

        e2 = _edge_count(c2, o2)
        score = -_quick_eval_edges(c2, o2, e2)
        score -= 15 * e2

        # Strongly avoid allowing the opponent to end the game immediately.
        if _immediate_win_exists(c2, o2):
            score -= 350000

        f = mv // N
        t = mv - f * N
        score += 4 * (_DEG[f] + _DEG[t])
        score += ((mv * 1315423911 + c - o) & 15)

        if score > best_score:
            best_score = score
            best = mv

    return best


# ---------------------------------------------------------------------
# Alpha-beta search
# ---------------------------------------------------------------------

def _negamax(c: int, o: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global _NODES, _TT

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    if not _has_moves(c, o):
        return -WIN + ply

    # Solve small endgames exactly when possible.
    occ = (c | o).bit_count()
    if occ <= 14 and depth < occ:
        depth = occ

    if depth <= 0:
        return _static_eval(c, o)

    key = c | (o << 30)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        stored_depth, flag, val, bm = entry
        tt_move = bm
        if stored_depth >= depth:
            if flag == 0:       # exact
                return val
            elif flag == 1:     # lower bound
                if val > alpha:
                    alpha = val
            else:               # upper bound
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    alpha0 = alpha
    beta0 = beta
    best = -INF
    best_move = -1

    for mv in _ordered_moves(c, o, tt_move):
        c2, o2 = _apply(c, o, mv)
        val = -_negamax(c2, o2, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_move == -1:
        return -WIN + ply

    if best <= alpha0:
        flag = 2      # upper
    elif best >= beta0:
        flag = 1      # lower
    else:
        flag = 0      # exact

    old = _TT.get(key)
    if len(_TT) < 400000 and (old is None or depth >= old[0]):
        _TT[key] = (depth, flag, best, best_move)

    return best


def _search_root(c: int, o: int, depth: int, preferred: int):
    if time.perf_counter() > _DEADLINE:
        raise _Timeout()

    moves = _ordered_moves(c, o, preferred)
    if not moves:
        return -INF, -1

    best = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    for mv in moves:
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()

        c2, o2 = _apply(c, o, mv)
        val = -_negamax(c2, o2, depth - 1, -beta, -alpha, 1)

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

    return best, best_move


# ---------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------

def policy(you: list[int], opponent: list[int]) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        # Last-resort safety: still return a legal move if one exists.
        try:
            c = _to_mask(you)
            o = _to_mask(opponent)
            c &= ~o
            moves = _gen_moves(c, o)
            if moves:
                return _MOVE_STR[moves[0]]
        except Exception:
            pass
        return "0,0,U"


def _policy_impl(you, opponent) -> str:
    global _TT, _DEADLINE, _NODES

    c = _to_mask(you)
    o = _to_mask(opponent)
    c &= ~o

    moves = _gen_moves(c, o)
    if not moves:
        # No legal move exists; the game should normally not ask in this state.
        return "0,0,U"

    ordered = _ordered_moves(c, o, -1)

    # Instant win check.
    for mv in ordered:
        c2, o2 = _apply(c, o, mv)
        if not _has_moves(c2, o2):
            return _MOVE_STR[mv]

    fallback = _heuristic_root_move(c, o, ordered)
    best = fallback
    preferred = fallback

    _TT = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.88

    total = (c | o).bit_count()

    for depth in range(1, total + 1):
        try:
            score, mv = _search_root(c, o, depth, preferred)
            if mv != -1:
                best = mv
                preferred = mv

            # A mate-score means the search proved a forced terminal result.
            if abs(score) > WIN // 2:
                break

            if time.perf_counter() > _DEADLINE:
                break

        except _Timeout:
            break

    if best == -1 or not _MOVE_STR[best]:
        best = moves[0]

    return _MOVE_STR[best]
