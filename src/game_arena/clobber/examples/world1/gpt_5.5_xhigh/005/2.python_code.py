
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

_WIN = 1_000_000
_INF = 1_000_000_000

_EXACT, _LOWER, _UPPER = 0, 1, 2
_EXACT_PIECES = 12
_STRIP_LIMIT = 18
_TT_LIMIT = 500_000

_ADJ = [0] * N
_POS = [0] * N
_DIR_FROM_DELTA = {-COLS: "U", 1: "R", COLS: "D", -1: "L"}

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        m = 0
        if r > 0:
            m |= 1 << (i - COLS)
        if c + 1 < COLS:
            m |= 1 << (i + 1)
        if r + 1 < ROWS:
            m |= 1 << (i + COLS)
        if c > 0:
            m |= 1 << (i - 1)
        _ADJ[i] = m

        # Mild centrality tie-breaker.
        _POS[i] = 20 - abs(2 * r - (ROWS - 1)) - abs(2 * c - (COLS - 1))

_TT = {}
_HIST = [0] * 1024
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _to_mask(board):
    """Accepts nested lists, flat lists, or numpy-like arrays."""
    m = 0
    shape = getattr(board, "shape", None)

    if shape is not None:
        try:
            if len(shape) >= 2:
                for r in range(ROWS):
                    for c in range(COLS):
                        if board[r, c]:
                            m |= 1 << (r * COLS + c)
                return m
            else:
                flat = board.ravel()
                for i in range(min(N, len(flat))):
                    if flat[i]:
                        m |= 1 << i
                return m
        except Exception:
            pass

    try:
        if len(board) == N:
            first = board[0]
            if not hasattr(first, "__len__"):
                for i in range(N):
                    if board[i]:
                        m |= 1 << i
                return m
    except Exception:
        pass

    try:
        for r in range(ROWS):
            row = board[r]
            for c in range(COLS):
                if row[c]:
                    m |= 1 << (r * COLS + c)
        return m
    except Exception:
        pass

    try:
        flat = list(board)
        for i in range(min(N, len(flat))):
            if flat[i]:
                m |= 1 << i
    except Exception:
        return 0

    return m


def _move_to_str(code):
    i = code >> 5
    j = code & 31
    d = _DIR_FROM_DELTA.get(j - i, "U")
    return f"{i // COLS},{i % COLS},{d}"


def _contacts(p, o):
    """Number of adjacent opposite-color pairs."""
    if p.bit_count() <= o.bit_count():
        x, other = p, o
    else:
        x, other = o, p

    s = 0
    while x:
        b = x & -x
        i = b.bit_length() - 1
        s += (_ADJ[i] & other).bit_count()
        x ^= b
    return s


def _strip_dead_components(p, o):
    """
    Disconnected monochrome components can never interact with the live game.
    Removing them preserves the winner and improves table/cache quality.
    """
    occ = p | o
    rem = occ
    keep = 0

    while rem:
        seed = rem & -rem
        comp = 0
        frontier = seed

        while frontier:
            comp |= frontier
            nb = 0
            y = frontier
            while y:
                b = y & -y
                nb |= _ADJ[b.bit_length() - 1]
                y ^= b
            frontier = nb & occ & ~comp

        if (comp & p) and (comp & o):
            keep |= comp

        rem &= ~comp

    return p & keep, o & keep


def _component_parity_score(p, o):
    """Small, low-weight heuristic for active component parity."""
    occ = p | o
    rem = occ
    estimated_moves = 0
    comps = 0
    balance = 0

    while rem:
        seed = rem & -rem
        comp = 0
        frontier = seed

        while frontier:
            comp |= frontier
            nb = 0
            y = frontier
            while y:
                b = y & -y
                nb |= _ADJ[b.bit_length() - 1]
                y ^= b
            frontier = nb & occ & ~comp

        cp_bits = comp & p
        co_bits = comp & o
        if cp_bits and co_bits:
            cp = cp_bits.bit_count()
            co = co_bits.bit_count()
            comps += 1
            estimated_moves += cp + co - 1
            balance += cp - co

        rem &= ~comp

    if comps == 0:
        return -100

    s = 28 if (estimated_moves & 1) else -28
    if comps > 1:
        s //= min(comps, 3)
    return s + 2 * balance


def _tt_save(key, depth, value, flag, move):
    old = _TT.get(key)
    if old is None or depth >= old[0] or depth >= 90:
        _TT[key] = (depth, value, flag, move)


def _has_immediate_win(p, o, e=None):
    """True if side p can move so the next side has no legal moves."""
    if e is None:
        e = _contacts(p, o)
    if e == 0:
        return False

    x = p
    while x:
        b = x & -x
        i = b.bit_length() - 1
        x ^= b

        n = _ADJ[i] & o
        if not n:
            continue

        d_from = n.bit_count()
        y = n
        while y:
            bj = y & -y
            j = bj.bit_length() - 1
            y ^= bj

            # Contacts after moving i -> j.
            new_e = (
                e
                - d_from
                - (_ADJ[j] & p).bit_count()
                + 1
                + (_ADJ[j] & o).bit_count()
            )
            if new_e == 0:
                return True

    return False


def _gen_moves(p, o, e, ttmove=-1):
    """
    Return sorted list of (ordering_score, move_code, contacts_after_move).
    move_code packs from/to as (from << 5) | to.
    """
    moves = []
    x = p

    while x:
        b = x & -x
        i = b.bit_length() - 1
        x ^= b

        n = _ADJ[i] & o
        if not n:
            continue

        d_from = n.bit_count()
        y = n
        while y:
            bj = y & -y
            j = bj.bit_length() - 1
            y ^= bj

            d_targ = (_ADJ[j] & p).bit_count()
            same_opp_near_target = (_ADJ[j] & o).bit_count()
            new_e = e - d_from - d_targ + 1 + same_opp_near_target

            code = (i << 5) | j

            if new_e == 0:
                order = 2_000_000_000
            else:
                order = (
                    -10_000 * new_e
                    + 90 * (d_from + d_targ)
                    - 45 * same_opp_near_target
                    + (_POS[j] - _POS[i])
                    + _HIST[code]
                )

            if code == ttmove:
                order += 1_000_000_000

            moves.append((order, code, new_e))

    moves.sort(reverse=True)
    return moves


def _static_eval(p, o, moves, e):
    """
    Tactical horizon evaluator from the side-to-move perspective.
    It favors positions where the mover can leave the opponent few replies,
    and detects exact loss-in-one-ply-response traps.
    """
    best_after = 99
    safe_best = 99
    low1 = low2 = low3 = 0
    safe_count = danger_count = 0

    total = (p | o).bit_count()
    check_danger = e <= 12 or total <= 16

    for _, code, ne in moves:
        if ne == 0:
            return _WIN

        if ne < best_after:
            best_after = ne

        if ne <= 1:
            low1 += 1
        elif ne == 2:
            low2 += 1
        elif ne <= 4:
            low3 += 1

        if check_danger:
            i = code >> 5
            j = code & 31
            ib = 1 << i
            jb = 1 << j
            p_after = (p ^ ib) | jb
            o_after = o ^ jb

            # Opponent's perspective after our move.
            if _has_immediate_win(o_after, p_after, ne):
                danger_count += 1
            else:
                safe_count += 1
                if ne < safe_best:
                    safe_best = ne

    if check_danger and safe_count == 0:
        return -_WIN + 1

    target = safe_best if safe_count else best_after
    if target < 1:
        target = 1

    pc = p.bit_count()
    oc = o.bit_count()

    score = 90
    score += 240 // target
    score -= 8 * target
    score += 3 * e
    score += 45 * low1 + 20 * low2 + 8 * low3

    if check_danger:
        score += 24 * safe_count - 32 * danger_count

    score += 2 * (pc - oc)

    # Degree distribution: opponent stones with many adjacent friendly stones
    # are vulnerable targets; our highly exposed stones are liabilities.
    vp = vo = 0

    x = p
    while x:
        b = x & -x
        i = b.bit_length() - 1
        d = (_ADJ[i] & o).bit_count()
        vp += d * d
        x ^= b

    x = o
    while x:
        b = x & -x
        i = b.bit_length() - 1
        d = (_ADJ[i] & p).bit_count()
        vo += d * d
        x ^= b

    score += 2 * (vo - vp)

    if total <= 18:
        score += _component_parity_score(p, o)

    if score > _WIN // 4:
        return _WIN // 4
    if score < -_WIN // 4:
        return -_WIN // 4
    return score


def _search(p, o, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout()

    total = (p | o).bit_count()
    if total <= _STRIP_LIMIT:
        sp, so = _strip_dead_components(p, o)
        if sp != p or so != o:
            p, o = sp, so
            total = (p | o).bit_count()

    if total <= _EXACT_PIECES and depth < total:
        depth = total

    key = p | (o << N)
    entry = _TT.get(key)
    ttmove = -1

    if entry is not None:
        edepth, eval_, eflag, emove = entry
        ttmove = emove
        if edepth >= depth:
            if eflag == _EXACT:
                return eval_
            if eflag == _LOWER:
                if eval_ > alpha:
                    alpha = eval_
            elif eflag == _UPPER:
                if eval_ < beta:
                    beta = eval_
            if alpha >= beta:
                return eval_

    e = _contacts(p, o)
    if e == 0:
        _tt_save(key, 99, -_WIN, _EXACT, -1)
        return -_WIN

    moves = _gen_moves(p, o, e, ttmove)
    if not moves:
        _tt_save(key, 99, -_WIN, _EXACT, -1)
        return -_WIN

    if moves[0][2] == 0:
        _tt_save(key, 99, _WIN, _EXACT, moves[0][1])
        return _WIN

    if depth <= 0:
        val = _static_eval(p, o, moves, e)
        _tt_save(key, 0, val, _EXACT, moves[0][1])
        return val

    alpha0 = alpha
    best_val = -_INF
    best_move = moves[0][1]
    first = True

    for _, code, _ in moves:
        i = code >> 5
        j = code & 31
        ib = 1 << i
        jb = 1 << j

        p_after = (p ^ ib) | jb
        o_after = o ^ jb

        if first:
            val = -_search(o_after, p_after, depth - 1, -beta, -alpha)
            first = False
        else:
            val = -_search(o_after, p_after, depth - 1, -alpha - 1, -alpha)
            if alpha < val < beta:
                val = -_search(o_after, p_after, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = code

        if val > alpha:
            alpha = val

        if alpha >= beta:
            nh = _HIST[code] + depth * depth
            _HIST[code] = nh if nh < 2_000_000 else 2_000_000
            break

    if best_val <= alpha0:
        flag = _UPPER
    elif best_val >= beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _tt_save(key, depth, best_val, flag, best_move)
    return best_val


def _fallback_from_masks(p, o):
    """Simple guaranteed legal move finder if any legal move exists."""
    best_code = -1
    best_score = -_INF

    x = p
    while x:
        b = x & -x
        i = b.bit_length() - 1
        x ^= b

        n = _ADJ[i] & o
        while n:
            bj = n & -n
            j = bj.bit_length() - 1
            n ^= bj

            code = (i << 5) | j
            score = _POS[j] - _POS[i]
            if score > best_score:
                best_score = score
                best_code = code

    if best_code >= 0:
        return _move_to_str(best_code)

    # Terminal positions should not be queried by the arena; no legal move exists.
    return "0,0,U"


def _policy_impl(you, opponent):
    global _DEADLINE, _NODES

    p0 = _to_mask(you)
    o0 = _to_mask(opponent)

    p, o = _strip_dead_components(p0, o0)
    e = _contacts(p, o)

    if e == 0:
        return _fallback_from_masks(p0, o0)

    root_moves = _gen_moves(p, o, e, -1)
    if not root_moves:
        return _fallback_from_masks(p0, o0)

    best_code = root_moves[0][1]

    if len(root_moves) == 1 or root_moves[0][2] == 0:
        return _move_to_str(best_code)

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    start = time.perf_counter()
    total = (p | o).bit_count()

    # Conservative time budget to stay safely below the 1-second arena limit.
    budget = 0.90
    if e <= 12 or total <= 16:
        budget = 0.94
    _DEADLINE = start + budget
    _NODES = 0

    root_codes = [m[1] for m in root_moves]
    root_order = {m[1]: m[0] for m in root_moves}
    last_scores = {}

    completed_best = best_code
    completed_val = -_INF

    max_depth = max(1, total)

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= _DEADLINE:
            break

        try:
            root_codes.sort(
                key=lambda c: (
                    1 if c == completed_best else 0,
                    last_scores.get(c, -_INF),
                    root_order.get(c, 0),
                    _HIST[c],
                ),
                reverse=True,
            )

            alpha = -_INF
            beta = _INF
            cur_best = root_codes[0]
            cur_val = -_INF
            scores = []
            first = True

            for code in root_codes:
                if (_NODES & 255) == 0 and time.perf_counter() >= _DEADLINE:
                    raise _Timeout()

                i = code >> 5
                j = code & 31
                ib = 1 << i
                jb = 1 << j

                p_after = (p ^ ib) | jb
                o_after = o ^ jb

                if first:
                    val = -_search(o_after, p_after, depth - 1, -beta, -alpha)
                    first = False
                else:
                    val = -_search(o_after, p_after, depth - 1, -alpha - 1, -alpha)
                    if alpha < val < beta:
                        val = -_search(o_after, p_after, depth - 1, -beta, -alpha)

                scores.append((val, code))

                if val > cur_val:
                    cur_val = val
                    cur_best = code

                if val > alpha:
                    alpha = val

            completed_best = cur_best
            completed_val = cur_val

            scores.sort(reverse=True)
            last_scores = {code: val for val, code in scores}
            root_codes = [code for val, code in scores]

            if completed_val >= _WIN // 2 or depth >= total:
                break

        except _Timeout:
            break

    return _move_to_str(completed_best)


def policy(you: list[int], opponent: list[int]) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        try:
            return _fallback_from_masks(_to_mask(you), _to_mask(opponent))
        except Exception:
            return "0,0,U"
