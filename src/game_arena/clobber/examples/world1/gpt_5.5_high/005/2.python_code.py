
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
FULL = (1 << N) - 1

COL0 = 0
COL5 = 0
ROW0 = 0
ROW4 = 0
for r in range(ROWS):
    COL0 |= 1 << (r * COLS)
    COL5 |= 1 << (r * COLS + COLS - 1)
for c in range(COLS):
    ROW0 |= 1 << c
    ROW4 |= 1 << ((ROWS - 1) * COLS + c)

NOT_COL0 = FULL ^ COL0
NOT_COL5 = FULL ^ COL5
NOT_ROW0 = FULL ^ ROW0
NOT_ROW4 = FULL ^ ROW4

NEIGHBORS = [0] * N
CENTER = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        m = 0
        if r > 0:
            m |= 1 << ((r - 1) * COLS + c)
        if r + 1 < ROWS:
            m |= 1 << ((r + 1) * COLS + c)
        if c > 0:
            m |= 1 << (r * COLS + c - 1)
        if c + 1 < COLS:
            m |= 1 << (r * COLS + c + 1)
        NEIGHBORS[i] = m
        # Small integer centrality bonus.
        CENTER[i] = 20 - 3 * ((r - 2) * (r - 2)) - abs(2 * c - 5)

WIN = 1_000_000
INF = 1_000_000_000
TIME_LIMIT = 0.93

EXACT = 0
LOWER = 1
UPPER = 2

_TT = {}
_HISTORY = [[0] * N for _ in range(N)]
_deadline = 0.0
_nodes = 0


class _SearchTimeout(Exception):
    pass


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _SearchTimeout()


def _bits(board):
    """Accepts nested lists, flat lists, or numpy-like arrays."""
    b = 0
    if hasattr(board, "ravel"):
        flat = board.ravel()
        for i, v in enumerate(flat):
            if i >= N:
                break
            if int(v) != 0:
                b |= 1 << i
        return b

    try:
        first = board[0]
        if hasattr(first, "__iter__") and not isinstance(first, (int, bool)):
            idx = 0
            for r in range(ROWS):
                row = board[r]
                for c in range(COLS):
                    if int(row[c]) != 0:
                        b |= 1 << idx
                    idx += 1
            return b
    except Exception:
        pass

    for i, v in enumerate(board):
        if i >= N:
            break
        if int(v) != 0:
            b |= 1 << i
    return b


def _adjacent_bits(bits):
    return (
        ((bits & NOT_COL5) << 1)
        | ((bits & NOT_COL0) >> 1)
        | ((bits & NOT_ROW4) << COLS)
        | ((bits & NOT_ROW0) >> COLS)
    ) & FULL


def _contact_count(me, opp):
    # Number of orthogonally adjacent unlike pairs.
    return (
        ((((me & NOT_COL5) << 1) & opp).bit_count())
        + ((((opp & NOT_COL5) << 1) & me).bit_count())
        + ((((me & NOT_ROW4) << COLS) & opp).bit_count())
        + ((((opp & NOT_ROW4) << COLS) & me).bit_count())
    )


def _same_edges(bits):
    return (
        ((((bits & NOT_COL5) << 1) & bits).bit_count())
        + ((((bits & NOT_ROW4) << COLS) & bits).bit_count())
    )


def _weight_sum(bits):
    s = 0
    while bits:
        lsb = bits & -bits
        i = lsb.bit_length() - 1
        s += CENTER[i]
        bits ^= lsb
    return s


def _generate_moves(me, opp):
    moves = []
    b = me
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        targets = NEIGHBORS[i] & opp
        while targets:
            t = targets & -targets
            j = t.bit_length() - 1
            targets ^= t
            moves.append((i, j))
    return moves


def _child(me, opp, i, j):
    bi = 1 << i
    bj = 1 << j
    # Return from next player's perspective.
    child_me = opp ^ bj
    child_opp = (me ^ bi) | bj
    return child_me, child_opp


def _move_to_str(i, j):
    d = j - i
    if d == -COLS:
        ch = "U"
    elif d == 1:
        ch = "R"
    elif d == COLS:
        ch = "D"
    else:
        ch = "L"
    return f"{i // COLS},{i % COLS},{ch}"


def _quick_eval(me, opp):
    c = _contact_count(me, opp)
    if c == 0:
        return -WIN

    my = me.bit_count()
    op = opp.bit_count()
    active_me = (me & _adjacent_bits(opp)).bit_count()
    active_opp = (opp & _adjacent_bits(me)).bit_count()

    score = 95 * (my - op)
    score += 28 * (active_me - active_opp)
    score += 15 * (_same_edges(me) - _same_edges(opp))
    score += 4 * (_weight_sum(me) - _weight_sum(opp))
    score += 3 * c
    score += 12  # tempo

    # Crude race/parity estimate if the mixed area remains connected enough.
    if my > 0 and op > 0:
        est = (2 * op - 1) if my >= op else (2 * my)
        score += 25 if (est & 1) else -25

    if score > WIN // 3:
        return WIN // 3
    if score < -WIN // 3:
        return -WIN // 3
    return score


def _has_immediate_win(me, opp):
    for i, j in _generate_moves(me, opp):
        cm, co = _child(me, opp, i, j)
        if _contact_count(cm, co) == 0:
            return True
    return False


def _all_moves_allow_immediate_loss(me, opp):
    any_move = False
    for i, j in _generate_moves(me, opp):
        any_move = True
        cm, co = _child(me, opp, i, j)
        if _contact_count(cm, co) == 0:
            return False
        if not _has_immediate_win(cm, co):
            return False
    return any_move


def _component_eval(me, opp):
    occ = me | opp
    unseen = occ
    mixed_diff = 0
    comp_score = 0
    est_moves = 0

    while unseen:
        seed = unseen & -unseen
        frontier = seed
        comp = 0
        while frontier:
            comp |= frontier
            unseen &= ~frontier
            frontier = _adjacent_bits(frontier) & occ & ~comp

        mbits = comp & me
        obits = comp & opp
        if mbits and obits:
            m = mbits.bit_count()
            o = obits.bit_count()
            mixed_diff += m - o

            if m > o:
                comp_score += 32
            elif m < o:
                comp_score -= 32

            if m >= o:
                est_moves += 2 * o - 1
            else:
                est_moves += 2 * m

    return mixed_diff, comp_score, est_moves


def _static_eval(me, opp):
    c = _contact_count(me, opp)
    if c == 0:
        return -WIN

    my = me.bit_count()
    op = opp.bit_count()
    active_me = (me & _adjacent_bits(opp)).bit_count()
    active_opp = (opp & _adjacent_bits(me)).bit_count()
    mixed_diff, comp_score, est_moves = _component_eval(me, opp)

    score = 35 * (my - op)              # dead pieces matter only a little
    score += 150 * mixed_diff           # live mixed-component material matters a lot
    score += 30 * (active_me - active_opp)
    score += 18 * (_same_edges(me) - _same_edges(opp))
    score += 5 * (_weight_sum(me) - _weight_sum(opp))
    score += 2 * c
    score += comp_score
    score += 14                         # side-to-move initiative

    if est_moves:
        score += 45 if (est_moves & 1) else -45

    # Tactical one-ply facts near quiet/endgame positions.
    if c <= 6:
        if _has_immediate_win(me, opp):
            return WIN // 2 + max(-10_000, min(10_000, score))
        if c <= 4 and _all_moves_allow_immediate_loss(me, opp):
            return -WIN // 2 + max(-10_000, min(10_000, score))

    if score > WIN // 3:
        return WIN // 3
    if score < -WIN // 3:
        return -WIN // 3
    return score


def _move_order_score(me, opp, i, j, tt_move):
    cm, co = _child(me, opp, i, j)
    score = -_quick_eval(cm, co)

    if tt_move is not None and i == tt_move[0] and j == tt_move[1]:
        score += 5_000_000

    # Capturing a piece supported by opponent friends often allows recapture.
    target_support = (NEIGHBORS[j] & opp).bit_count()
    other_attackers = (NEIGHBORS[j] & me).bit_count() - 1
    source_danger = (NEIGHBORS[i] & opp).bit_count() - 1

    if target_support > 0:
        score -= 24 * target_support
    if other_attackers > 0:
        score += 14 * other_attackers
    if source_danger > 0:
        score += 9 * source_danger

    score += 2 * (CENTER[j] - CENTER[i])
    score += _HISTORY[i][j]
    return score


def _ordered_moves(me, opp, tt_move=None):
    arr = []
    b = me
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        targets = NEIGHBORS[i] & opp
        while targets:
            t = targets & -targets
            j = t.bit_length() - 1
            targets ^= t
            arr.append((_move_order_score(me, opp, i, j, tt_move), i, j))
    arr.sort(reverse=True)
    return arr


def _negamax(me, opp, depth, alpha, beta):
    _check_time()

    c = _contact_count(me, opp)
    if c == 0:
        return -WIN
    if depth <= 0:
        return _static_eval(me, opp)

    alpha0 = alpha
    beta0 = beta
    key = (me, opp)
    entry = _TT.get(key)
    tt_move = None

    if entry is not None:
        edepth, eflag, escore, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return escore
            if eflag == LOWER:
                if escore > alpha:
                    alpha = escore
            elif eflag == UPPER:
                if escore < beta:
                    beta = escore
            if alpha >= beta:
                return escore

    moves = _ordered_moves(me, opp, tt_move)
    if not moves:
        return -WIN

    best_score = -INF
    best_move = (moves[0][1], moves[0][2])
    first = True

    for _, i, j in moves:
        cm, co = _child(me, opp, i, j)

        if first:
            score = -_negamax(cm, co, depth - 1, -beta, -alpha)
            first = False
        else:
            # Principal variation search.
            score = -_negamax(cm, co, depth - 1, -alpha - 1, -alpha)
            if alpha < score < beta:
                score = -_negamax(cm, co, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = (i, j)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if _HISTORY[i][j] < 1_000_000:
                _HISTORY[i][j] += depth * depth
            break

    if best_score <= alpha0:
        flag = UPPER
    elif best_score >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    _TT[key] = (depth, flag, best_score, best_move)
    return best_score


def _search_root(me, opp, depth, root_order):
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = (root_order[0][1], root_order[0][2])
    new_order = []
    first = True

    for _, i, j in root_order:
        _check_time()
        cm, co = _child(me, opp, i, j)

        if first:
            score = -_negamax(cm, co, depth - 1, -beta, -alpha)
            first = False
        else:
            score = -_negamax(cm, co, depth - 1, -alpha - 1, -alpha)
            if alpha < score < beta:
                score = -_negamax(cm, co, depth - 1, -beta, -alpha)

        new_order.append((score, i, j))

        if score > best_score:
            best_score = score
            best_move = (i, j)
        if score > alpha:
            alpha = score

    new_order.sort(reverse=True)
    return best_score, best_move, new_order


def _policy_impl(you, opponent):
    global _deadline, _nodes, _TT

    me = _bits(you)
    opp = _bits(opponent) & ~me

    raw_moves = _generate_moves(me, opp)
    if not raw_moves:
        # No legal move exists in a terminal losing state. This should not be
        # requested by the arena, but keep a syntactically valid fallback.
        return "0,0,U"

    if len(_TT) > 350_000:
        _TT.clear()

    # If a move immediately leaves the opponent with no legal move, play it.
    for i, j in raw_moves:
        cm, co = _child(me, opp, i, j)
        if _contact_count(cm, co) == 0:
            return _move_to_str(i, j)

    if len(raw_moves) == 1:
        return _move_to_str(raw_moves[0][0], raw_moves[0][1])

    _deadline = time.perf_counter() + TIME_LIMIT
    _nodes = 0

    root_order = _ordered_moves(me, opp, None)
    last_best = (root_order[0][1], root_order[0][2])

    total = (me | opp).bit_count()
    max_depth = max(1, total)

    for depth in range(1, max_depth + 1):
        try:
            score, best, root_order = _search_root(me, opp, depth, root_order)
            last_best = best

            # Exact forced win found within the searched horizon.
            if score >= WIN:
                break
            if time.perf_counter() > _deadline:
                break
        except _SearchTimeout:
            break

    return _move_to_str(last_best[0], last_best[1])


def policy(you: list[int], opponent: list[int]) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        # Last-resort safety: return the first legal move if anything unexpected
        # happens. The arena values legality above all else.
        try:
            me = _bits(you)
            opp = _bits(opponent) & ~me
            moves = _generate_moves(me, opp)
            if moves:
                return _move_to_str(moves[0][0], moves[0][1])
        except Exception:
            pass
        return "0,0,U"
