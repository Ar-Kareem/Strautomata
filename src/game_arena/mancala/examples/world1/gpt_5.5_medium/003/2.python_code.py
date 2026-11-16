
import time
import sys

sys.setrecursionlimit(10000)

# Ring positions relative to the active player:
# active houses 0..5, active store 6, passive houses 0..5.
_RING = (
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)
)

_INF = 10 ** 18


class _Timeout(Exception):
    pass


def _legal(side_board):
    return [i for i in range(6) if side_board[i] > 0]


def _terminal_value(a, b):
    """Return exact terminal value from root player's perspective, or None."""
    sa = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    sb = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    if sa == 0 or sb == 0:
        return ((a[6] + sa) - (b[6] + sb)) * 100000
    return None


def _apply_move(a, b, side, move):
    """
    Apply move for side 0/root or side 1/opponent.
    Returns: new_a, new_b, next_side, terminal_bool
    """
    if side == 0:
        active = list(a)
        passive = list(b)
    else:
        active = list(b)
        passive = list(a)

    seeds = active[move]
    active[move] = 0
    idx = move

    while seeds:
        idx += 1
        if idx == 13:
            idx = 0
        s, p = _RING[idx]
        if s == 0:
            active[p] += 1
        else:
            passive[p] += 1
        seeds -= 1

    last_side, last_pos = _RING[idx]

    # Capture: last seed in active empty house, opposite passive house non-empty.
    if last_side == 0 and last_pos < 6 and active[last_pos] == 1:
        opp = 5 - last_pos
        if passive[opp] > 0:
            active[6] += active[last_pos] + passive[opp]
            active[last_pos] = 0
            passive[opp] = 0

    extra = (last_side == 0 and last_pos == 6)

    # Game end sweep.
    active_houses = active[0] + active[1] + active[2] + active[3] + active[4] + active[5]
    passive_houses = passive[0] + passive[1] + passive[2] + passive[3] + passive[4] + passive[5]
    terminal = False
    if active_houses == 0 or passive_houses == 0:
        terminal = True
        active[6] += active_houses
        passive[6] += passive_houses
        for i in range(6):
            active[i] = 0
            passive[i] = 0

    if side == 0:
        na, nb = tuple(active), tuple(passive)
    else:
        na, nb = tuple(passive), tuple(active)

    next_side = side if extra and not terminal else 1 - side
    return na, nb, next_side, terminal


def _extra_count(board):
    c = 0
    for i in range(6):
        s = board[i]
        if s > 0 and (i + s) % 13 == 6:
            c += 1
    return c


def _approx_capture(active, passive):
    """Lightweight estimate of best immediate capture available."""
    best = 0
    for i in range(6):
        s = active[i]
        if s <= 0:
            continue
        last = (i + s) % 13
        if 0 <= last < 6:
            # Exact for common no-full-lap cases; still useful as an estimate.
            if last != i and active[last] == 0 and passive[5 - last] > 0:
                gain = passive[5 - last] + 1
                if gain > best:
                    best = gain
    return best


def _heuristic(a, b):
    """
    Non-terminal evaluation from root player's perspective.
    Store lead dominates; other terms guide horizon positions.
    """
    tv = _terminal_value(a, b)
    if tv is not None:
        return tv

    ah = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    bh = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]

    score = (a[6] - b[6]) * 100
    score += (ah - bh) * 3

    # Seeds nearer to the store are often more flexible/valuable.
    positional = 0
    for i in range(6):
        positional += (i + 1) * (a[i] - b[i])
    score += positional

    # Horizon guidance for free turns and captures.
    score += 18 * (_extra_count(a) - _extra_count(b))
    score += 8 * (_approx_capture(a, b) - _approx_capture(b, a))

    # Mobility is mildly useful.
    score += 2 * (len(_legal(a)) - len(_legal(b)))

    return score


def _ordered_children(a, b, side, tt_best=None):
    board = a if side == 0 else b
    moves = _legal(board)
    children = []

    for m in moves:
        na, nb, ns, term = _apply_move(a, b, side, m)
        val = _heuristic(na, nb)

        # Prefer known best move from transposition table.
        if tt_best == m:
            val += 10000000 if side == 0 else -10000000

        # Small ordering bonus/penalty for retaining the move.
        if ns == side and not term:
            val += 500 if side == 0 else -500

        children.append((val, m, na, nb, ns))

    children.sort(key=lambda x: x[0], reverse=(side == 0))
    return children


def policy(you: list[int], opponent: list[int]) -> int:
    start = time.perf_counter()
    deadline = start + 0.90

    a = tuple(int(x) for x in you)
    b = tuple(int(x) for x in opponent)

    legal_moves = _legal(a)
    # The problem guarantees at least one legal move, but keep a defensive guard.
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Strong known standard opening: third house gives an immediate extra turn.
    if a == (4, 4, 4, 4, 4, 4, 0) and b == (4, 4, 4, 4, 4, 4, 0):
        return 2

    # Tactical fallback, used if search times out unexpectedly.
    best_move = legal_moves[0]
    best_score = -_INF
    for m in legal_moves:
        na, nb, ns, term = _apply_move(a, b, 0, m)
        sc = _heuristic(na, nb)
        if ns == 0 and not term:
            sc += 700
        if sc > best_score:
            best_score = sc
            best_move = m

    tt = {}
    nodes = [0]

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 2047) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

    def alphabeta(aa, bb, side, depth, alpha, beta):
        check_time()

        tv = _terminal_value(aa, bb)
        if tv is not None:
            return tv
        if depth <= 0:
            return _heuristic(aa, bb)

        key = (aa, bb, side)
        entry = tt.get(key)
        tt_best = None
        if entry is not None:
            e_depth, e_val, e_flag, e_best = entry
            tt_best = e_best
            if e_depth >= depth:
                if e_flag == 0:       # exact
                    return e_val
                elif e_flag == 1:     # lower bound
                    if e_val > alpha:
                        alpha = e_val
                else:                 # upper bound
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        alpha0, beta0 = alpha, beta

        if side == 0:
            value = -_INF
            best_local = None
            for _, m, na, nb, ns in _ordered_children(aa, bb, side, tt_best):
                v = alphabeta(na, nb, ns, depth - 1, alpha, beta)
                if v > value:
                    value = v
                    best_local = m
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        else:
            value = _INF
            best_local = None
            for _, m, na, nb, ns in _ordered_children(aa, bb, side, tt_best):
                v = alphabeta(na, nb, ns, depth - 1, alpha, beta)
                if v < value:
                    value = v
                    best_local = m
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

        # Transposition table flag.
        if value <= alpha0:
            flag = 2   # upper bound
        elif value >= beta0:
            flag = 1   # lower bound
        else:
            flag = 0   # exact

        tt[key] = (depth, value, flag, best_local)
        return value

    # Iterative deepening.
    move_order = list(legal_moves)
    max_depth = 64

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            current_best = best_move
            current_score = -_INF
            scores = {}

            alpha = -_INF
            beta = _INF

            # Search previously promising root moves first.
            for m in move_order:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                na, nb, ns, term = _apply_move(a, b, 0, m)
                v = alphabeta(na, nb, ns, depth - 1, alpha, beta)
                scores[m] = v

                if v > current_score:
                    current_score = v
                    current_best = m

                if v > alpha:
                    alpha = v

            # Only commit after a fully completed depth.
            best_move = current_best
            best_score = current_score
            move_order.sort(key=lambda x: scores.get(x, -_INF), reverse=True)

            # If a forced terminal win is clearly found, no need to spend more.
            if best_score > 5000000:
                break

    except _Timeout:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        pass

    if best_move not in legal_moves or a[best_move] <= 0:
        return legal_moves[0]
    return int(best_move)
