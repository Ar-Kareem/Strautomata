
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

WIN = 1_000_000
INF = 1_000_000_000

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

TT_LIMIT = 300_000
CACHE_LIMIT = 150_000

BITS = [1 << i for i in range(N)]
ADJ = [0] * N
CELL_SCORE = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        # Mild tie-breaker: central squares tend to keep options open.
        CELL_SCORE[i] = 20 - (abs(r - 2) * 3 + abs((2 * c) - 5))
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                ADJ[i] |= 1 << (nr * COLS + nc)

_TT = {}
_EDGE_CACHE = {}
_ACTIVE_CACHE = {}
_COMP_CACHE = {}
_FINISH_CACHE = {}

_DEADLINE = 0.0
_NODES = 0


def _key(y, o):
    return y | (o << N)


def _to_bits(arr):
    """Accepts either a 5x6 nested array/list or a flat length-30 iterable."""
    b = 0
    try:
        for r in range(ROWS):
            row = arr[r]
            for c in range(COLS):
                if row[c]:
                    b |= 1 << (r * COLS + c)
        return b
    except Exception:
        pass

    b = 0
    idx = 0
    try:
        iterator = iter(arr)
    except TypeError:
        return 0

    for v in iterator:
        if idx >= N:
            break
        if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
            for x in v:
                if idx >= N:
                    break
                if x:
                    b |= 1 << idx
                idx += 1
        else:
            if v:
                b |= 1 << idx
            idx += 1
    return b


def _format_move(m):
    f = m >> 5
    t = m & 31
    diff = t - f
    if diff == -COLS:
        d = "U"
    elif diff == 1:
        d = "R"
    elif diff == COLS:
        d = "D"
    else:
        d = "L"
    return f"{f // COLS},{f % COLS},{d}"


def _gen_moves(y, o):
    moves = []
    yy = y
    while yy:
        lsb = yy & -yy
        i = lsb.bit_length() - 1
        targets = ADJ[i] & o
        while targets:
            tb = targets & -targets
            j = tb.bit_length() - 1
            moves.append((i << 5) | j)
            targets ^= tb
        yy ^= lsb
    return moves


def _child(y, o, m):
    f = m >> 5
    t = m & 31
    fb = 1 << f
    tb = 1 << t

    # Current player moves f -> t, capturing opponent at t.
    moved_current = (y ^ fb) | tb
    remaining_opp = o ^ tb

    # Next search node is from the opponent's perspective.
    return remaining_opp, moved_current


def _edge_count(y, o):
    """Number of adjacent opposing pairs. This equals legal move count for either side."""
    if not y or not o:
        return 0

    k1 = _key(y, o)
    k2 = _key(o, y)
    k = k1 if k1 < k2 else k2

    try:
        return _EDGE_CACHE[k]
    except KeyError:
        pass

    a, b = y, o
    if a.bit_count() > b.bit_count():
        a, b = b, a

    cnt = 0
    aa = a
    while aa:
        lsb = aa & -aa
        i = lsb.bit_length() - 1
        cnt += (ADJ[i] & b).bit_count()
        aa ^= lsb

    if len(_EDGE_CACHE) > CACHE_LIMIT:
        _EDGE_CACHE.clear()
    _EDGE_CACHE[k] = cnt
    return cnt


def _active_count(side, other):
    """Pieces of side that are adjacent to at least one opposing piece."""
    if not side or not other:
        return 0

    k = _key(side, other)
    try:
        return _ACTIVE_CACHE[k]
    except KeyError:
        pass

    cnt = 0
    ss = side
    while ss:
        lsb = ss & -ss
        i = lsb.bit_length() - 1
        if ADJ[i] & other:
            cnt += 1
        ss ^= lsb

    if len(_ACTIVE_CACHE) > CACHE_LIMIT:
        _ACTIVE_CACHE.clear()
    _ACTIVE_CACHE[k] = cnt
    return cnt


def _component_estimate(y, o):
    """
    For each occupied connected component, add min(own, opponent) if mixed.
    This is a useful lower-bound style estimate of how many captures remain
    before components become monochromatic/separated.
    """
    k = _key(y, o)
    try:
        return _COMP_CACHE[k]
    except KeyError:
        pass

    occ = y | o
    unseen = occ
    estimated_moves = 0
    majority_balance = 0
    mixed_components = 0

    while unseen:
        start = unseen & -unseen
        comp = 0
        frontier = start

        while frontier:
            comp |= frontier
            nb = 0
            ff = frontier
            while ff:
                lsb = ff & -ff
                i = lsb.bit_length() - 1
                nb |= ADJ[i]
                ff ^= lsb
            frontier = nb & occ & ~comp

        unseen &= ~comp

        cy = (comp & y).bit_count()
        co = (comp & o).bit_count()
        if cy and co:
            mixed_components += 1
            estimated_moves += cy if cy < co else co
            if cy > co:
                majority_balance += 1
            elif co > cy:
                majority_balance -= 1

    ans = (estimated_moves, majority_balance, mixed_components)

    if len(_COMP_CACHE) > CACHE_LIMIT:
        _COMP_CACHE.clear()
    _COMP_CACHE[k] = ans
    return ans


def _has_finishing_move(y, o, moves=None):
    """
    True if side to move can make a capture after which the opponent has no legal move.
    """
    k = _key(y, o)
    try:
        return _FINISH_CACHE[k]
    except KeyError:
        pass

    if moves is None:
        moves = _gen_moves(y, o)

    ans = False
    for m in moves:
        cy, co = _child(y, o, m)
        if _edge_count(cy, co) == 0:
            ans = True
            break

    if len(_FINISH_CACHE) > CACHE_LIMIT:
        _FINISH_CACHE.clear()
    _FINISH_CACHE[k] = ans
    return ans


def _quick_eval(y, o, edge=None):
    if edge is None:
        edge = _edge_count(y, o)
    if edge == 0:
        return -WIN

    yp = y.bit_count()
    op = o.bit_count()
    ya = _active_count(y, o)
    oa = _active_count(o, y)

    # More pieces and more active pieces for the side to move are usually good.
    return 90 * (yp - op) + 75 * (ya - oa)


def _evaluate(y, o, moves=None):
    if moves is None:
        moves = _gen_moves(y, o)

    edge = len(moves)
    if edge == 0:
        return -WIN

    # Exact tactical one-ply win.
    if edge <= 16 and _has_finishing_move(y, o, moves):
        return WIN - 1

    # Exact tactical two-ply loss: every move allows opponent to finish.
    if edge <= 12:
        all_bad = True
        for m in moves:
            cy, co = _child(y, o, m)
            cm = _gen_moves(cy, co)
            if not _has_finishing_move(cy, co, cm):
                all_bad = False
                break
        if all_bad:
            return -WIN + 1

    score = _quick_eval(y, o, edge)

    est, maj_bal, mixed = _component_estimate(y, o)

    # If the rough remaining-capture estimate is odd, side to move is favored.
    if est:
        parity_bonus = 220 + max(0, 4 - est) * 55
        if est & 1:
            score += parity_bonus
        else:
            score -= parity_bonus

    score += 35 * maj_bal
    score += 8 * mixed

    return score


def _order_moves(y, o, moves, tt_best=-1):
    if len(moves) <= 1:
        return moves

    scored = []
    for m in moves:
        cy, co = _child(y, o, m)
        edge = _edge_count(cy, co)

        if edge == 0:
            s = 10_000_000
        else:
            # Good for us means bad for the opponent at the child node.
            s = -_quick_eval(cy, co, edge)

            # Avoid moves that hand the opponent an immediate finish.
            if edge <= 8 and _has_finishing_move(cy, co):
                s -= 500_000

        if m == tt_best:
            s += 20_000_000

        f = m >> 5
        t = m & 31
        s += CELL_SCORE[t] - CELL_SCORE[f]

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError


def _negamax(y, o, depth, alpha, beta):
    _check_time()

    moves = _gen_moves(y, o)
    if not moves:
        return -WIN

    if depth <= 0:
        pieces = (y | o).bit_count()
        # Fully solve small endgames when reached at the horizon.
        if pieces <= 9:
            depth = pieces
        else:
            return _evaluate(y, o, moves)

    key = _key(y, o)
    tt_best = -1

    entry = _TT.get(key)
    if entry is not None:
        edepth, eval_, flag, emove = entry
        tt_best = emove
        if edepth >= depth:
            if flag == TT_EXACT:
                return eval_
            if flag == TT_LOWER and eval_ >= beta:
                return eval_
            if flag == TT_UPPER and eval_ <= alpha:
                return eval_

    alpha_orig = alpha
    beta_orig = beta

    ordered = _order_moves(y, o, moves, tt_best)
    best_val = -INF
    best_move = ordered[0]

    for m in ordered:
        cy, co = _child(y, o, m)
        val = -_negamax(cy, co, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = TT_UPPER
    elif best_val >= beta_orig:
        flag = TT_LOWER
    else:
        flag = TT_EXACT

    if len(_TT) < TT_LIMIT:
        _TT[key] = (depth, best_val, flag, best_move)

    return best_val


def _root_search(y, o, depth, preferred):
    moves = _gen_moves(y, o)
    ordered = _order_moves(y, o, moves, preferred)

    best = ordered[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    for m in ordered:
        cy, co = _child(y, o, m)
        val = -_negamax(cy, co, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best = m

        if val > alpha:
            alpha = val

    return best, best_val


def _best_heuristic(y, o, moves):
    best = moves[0]
    best_score = -INF

    for m in _order_moves(y, o, moves):
        cy, co = _child(y, o, m)
        cm = _gen_moves(cy, co)

        # Immediate terminal win.
        if not cm:
            return m

        score = -_evaluate(cy, co, cm)

        if score > best_score:
            best_score = score
            best = m

    return best


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES

    y = _to_bits(you)
    o = _to_bits(opponent) & ~y

    moves = _gen_moves(y, o)

    # If called in a terminal state, no legal move exists. This should not happen
    # during normal arena play, but return a syntactically valid string anyway.
    if not moves:
        return "0,0,U"

    # Avoid unbounded memory growth across many games.
    if len(_TT) > TT_LIMIT:
        _TT.clear()
    if len(_EDGE_CACHE) > CACHE_LIMIT:
        _EDGE_CACHE.clear()
    if len(_ACTIVE_CACHE) > CACHE_LIMIT:
        _ACTIVE_CACHE.clear()
    if len(_COMP_CACHE) > CACHE_LIMIT:
        _COMP_CACHE.clear()
    if len(_FINISH_CACHE) > CACHE_LIMIT:
        _FINISH_CACHE.clear()

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODES = 0

    # Always take an immediate winning move.
    for m in moves:
        cy, co = _child(y, o, m)
        if _edge_count(cy, co) == 0:
            return _format_move(m)

    # Legal fallback before any expensive search.
    best = _best_heuristic(y, o, moves)
    preferred = best

    max_depth = max(1, (y | o).bit_count())

    try:
        depth = 1
        while depth <= max_depth:
            b, _ = _root_search(y, o, depth, preferred)
            best = b
            preferred = b

            if time.perf_counter() > _DEADLINE - 0.02:
                break

            depth += 1

    except TimeoutError:
        pass
    except Exception:
        # Preserve the already-computed legal fallback/best move.
        pass

    return _format_move(best)
