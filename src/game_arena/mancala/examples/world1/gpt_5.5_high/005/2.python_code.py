
import time

_INF = 10 ** 60
_WIN_SCALE = 1_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT = {}
_MAX_TT = 300_000

_DEADLINE = 0.0
_NODES = 0
_CHECK_MASK = 1023
_PLY_LIMIT = 160

_PROGRESS_WEIGHTS = (0, 1, 2, 3, 4, 5)


class _Timeout(Exception):
    pass


def _sum6(a):
    return a[0] + a[1] + a[2] + a[3] + a[4] + a[5]


def _key(y, o):
    return (
        y[0], y[1], y[2], y[3], y[4], y[5], y[6],
        o[0], o[1], o[2], o[3], o[4], o[5], o[6],
    )


def _legal_moves(y):
    return [i for i in range(6) if y[i] > 0]


def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & _CHECK_MASK) == 0:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()


def _final_margin_known(y, o, sy, so):
    # If the game is terminal, all remaining house seeds are swept into stores.
    return (y[6] + sy) - (o[6] + so)


def _make_move(y, o, move):
    """Return (new_y, new_o, extra_turn). Does not mutate inputs."""
    seeds = y[move]
    ny = y.copy()
    no = o.copy()
    ny[move] = 0

    # Fast sowing over the 13 legal sowing locations:
    # own houses 0..5, own store 6, opponent houses 7..12.
    q, r = divmod(seeds, 13)

    if q:
        ny[0] += q
        ny[1] += q
        ny[2] += q
        ny[3] += q
        ny[4] += q
        ny[5] += q
        ny[6] += q
        no[0] += q
        no[1] += q
        no[2] += q
        no[3] += q
        no[4] += q
        no[5] += q

    pos = move
    for _ in range(r):
        pos += 1
        if pos == 13:
            pos = 0
        if pos < 6:
            ny[pos] += 1
        elif pos == 6:
            ny[6] += 1
        else:
            no[pos - 7] += 1

    last = (move + seeds) % 13
    extra = (last == 6)

    # Capture.
    if last < 6 and ny[last] == 1:
        opp_idx = 5 - last
        captured = no[opp_idx]
        if captured > 0:
            ny[6] += captured + 1
            ny[last] = 0
            no[opp_idx] = 0

    return ny, no, extra


def _side_features(a, b):
    legal = 0
    free = 0
    cap_best = 0
    cap_sum = 0
    trap = 0
    progress = 0

    for i in range(6):
        s = a[i]
        progress += _PROGRESS_WEIGHTS[i] * s

        if s > 0:
            legal += 1
            last = (i + s) % 13

            if last == 6:
                free += 1

            # A capture is possible only if the final own pit was empty
            # immediately before the last seed. For this board, that can only
            # happen with fewer than a full extra lap, or exactly 13 into the
            # starting pit.
            if last < 6 and s <= 13 and (last == i or a[last] == 0):
                opp = b[5 - last]
                if opp > 0:
                    gain = opp + 1
                    cap_sum += gain
                    if gain > cap_best:
                        cap_best = gain
        else:
            trap += b[5 - i]

    return legal, free, cap_best, cap_sum, trap, progress


def _terminal_options(a, b):
    """Terminal moves available to side a. Returns (best_margin, count, legal_count)."""
    best = -_INF
    count = 0
    legal_count = 0

    for m in range(6):
        if a[m] <= 0:
            continue
        legal_count += 1
        na, nb, _ = _make_move(a, b, m)
        sa = _sum6(na)
        sb = _sum6(nb)
        if sa == 0 or sb == 0:
            count += 1
            margin = _final_margin_known(na, nb, sa, sb)
            if margin > best:
                best = margin

    return best, count, legal_count


def _evaluate(y, o):
    sy = _sum6(y)
    so = _sum6(o)

    if sy == 0 or so == 0:
        return _final_margin_known(y, o, sy, so) * _WIN_SCALE

    store_diff = y[6] - o[6]
    score = 1000 * store_diff
    score += 80 * (sy - so)

    yf = _side_features(y, o)
    of = _side_features(o, y)

    y_legal, y_free, y_cap_best, y_cap_sum, y_trap, y_prog = yf
    o_legal, o_free, o_cap_best, o_cap_sum, o_trap, o_prog = of

    score += 6 * (y_prog - o_prog)
    score += 220 * y_free - 180 * o_free
    score += 90 * y_cap_best + 20 * y_cap_sum
    score -= 80 * o_cap_best + 18 * o_cap_sum
    score += 10 * y_trap - 8 * o_trap
    score += 8 * (y_legal - o_legal)

    remaining = sy + so
    if store_diff > remaining:
        score += 300_000
    elif -store_diff > remaining:
        score -= 300_000

    # If the side to move can end the game immediately, treat that as a
    # quiescent exact-ish tactical fact.
    if sy <= 8:
        best_end, end_count, legal_count = _terminal_options(y, o)
        if end_count:
            if end_count == legal_count:
                return best_end * _WIN_SCALE
            if best_end >= 0:
                v = best_end * _WIN_SCALE
                if v > score:
                    score = v

    return score


def _child_order_score(y, o, ny, no, extra, move, preferred):
    sy = _sum6(ny)
    so = _sum6(no)

    if sy == 0 or so == 0:
        score = _final_margin_known(ny, no, sy, so) * _WIN_SCALE
    else:
        delta_store = ny[6] - y[6]
        score = 1000 * (ny[6] - no[6])
        score += 80 * (sy - so)
        score += 300 * delta_store
        if extra:
            score += 50_000

    if move == preferred:
        score += 10 ** 18

    return score


def _ordered_children(y, o, legal, preferred=-1):
    children = []
    for m in legal:
        ny, no, extra = _make_move(y, o, m)
        score = _child_order_score(y, o, ny, no, extra, m, preferred)
        children.append((score, m, ny, no, extra))

    children.sort(key=lambda x: x[0], reverse=True)
    return [(m, ny, no, extra) for _, m, ny, no, extra in children]


def _negamax(y, o, depth, alpha, beta, ply):
    _tick()

    sy = _sum6(y)
    so = _sum6(o)

    if sy == 0 or so == 0:
        return _final_margin_known(y, o, sy, so) * _WIN_SCALE

    if depth <= 0 or ply >= _PLY_LIMIT:
        return _evaluate(y, o)

    key = _key(y, o)
    entry = _TT.get(key)
    preferred = -1

    if entry is not None:
        e_depth, e_flag, e_value, e_move = entry
        preferred = e_move

        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_value
            if e_flag == _LOWER:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _UPPER:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    alpha_orig = alpha
    beta_orig = beta

    legal = _legal_moves(y)
    if not legal:
        return _final_margin_known(y, o, sy, so) * _WIN_SCALE

    children = _ordered_children(y, o, legal, preferred)

    best = -_INF
    best_move = children[0][0]
    first = True

    for m, ny, no, extra in children:
        if first or alpha + 1 >= beta:
            if extra:
                value = _negamax(ny, no, depth, alpha, beta, ply + 1)
            else:
                value = -_negamax(no, ny, depth - 1, -beta, -alpha, ply + 1)
        else:
            # Principal variation search / null-window probe.
            if extra:
                value = _negamax(ny, no, depth, alpha, alpha + 1, ply + 1)
                if alpha < value < beta:
                    value = _negamax(ny, no, depth, alpha, beta, ply + 1)
            else:
                value = -_negamax(no, ny, depth - 1, -alpha - 1, -alpha, ply + 1)
                if alpha < value < beta:
                    value = -_negamax(no, ny, depth - 1, -beta, -alpha, ply + 1)

        first = False

        if value > best:
            best = value
            best_move = m

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = _UPPER
    elif best >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < _MAX_TT:
        _TT[key] = (depth, flag, best, best_move)

    return best


def _search_root(y, o, depth, preferred):
    legal = _legal_moves(y)
    key = _key(y, o)

    entry = _TT.get(key)
    if entry is not None:
        e_depth, e_flag, e_value, e_move = entry
        if e_depth >= depth and e_flag == _EXACT and e_move in legal:
            return e_value, e_move
        if preferred not in legal and e_move in legal:
            preferred = e_move

    children = _ordered_children(y, o, legal, preferred)

    best = -_INF
    best_move = children[0][0]
    alpha = -_INF
    beta = _INF

    for m, ny, no, extra in children:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()

        if extra:
            value = _negamax(ny, no, depth, alpha, beta, 1)
        else:
            value = -_negamax(no, ny, depth - 1, -beta, -alpha, 1)

        if value > best:
            best = value
            best_move = m

        if value > alpha:
            alpha = value

    if len(_TT) < _MAX_TT:
        _TT[key] = (depth, _EXACT, best, best_move)

    return best, best_move


def _greedy_move(y, o, legal):
    best_move = legal[0]
    best_value = -_INF

    for m in legal:
        ny, no, extra = _make_move(y, o, m)
        sy = _sum6(ny)
        so = _sum6(no)

        if sy == 0 or so == 0:
            value = _final_margin_known(ny, no, sy, so) * _WIN_SCALE
        elif extra:
            value = _evaluate(ny, no) + 30_000
        else:
            value = -_evaluate(no, ny)

        if value > best_value:
            best_value = value
            best_move = m

    return best_move


def _root_terminal_choice(y, o, legal):
    best_move = legal[0]
    best_margin = -_INF
    count = 0

    for m in legal:
        ny, no, _ = _make_move(y, o, m)
        sy = _sum6(ny)
        so = _sum6(no)

        if sy == 0 or so == 0:
            count += 1
            margin = _final_margin_known(ny, no, sy, so)
            if margin > best_margin:
                best_margin = margin
                best_move = m

    return best_move, best_margin, count


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    fallback = legal[0]

    try:
        fallback = _greedy_move(you, opponent, legal)

        # If every legal move ends the game, play the exact best one. If any
        # move wins immediately, take the guaranteed win.
        terminal_move, terminal_margin, terminal_count = _root_terminal_choice(you, opponent, legal)
        if terminal_count == len(legal):
            return terminal_move
        if terminal_count and terminal_margin > 0:
            return terminal_move

        if len(_TT) >= _MAX_TT:
            _TT.clear()

        _DEADLINE = time.perf_counter() + 0.88
        _NODES = 0

        best_move = fallback

        # Iterative deepening. Depth counts opponent-turn changes; extra moves
        # by the same side do not consume depth inside the search.
        for depth in range(1, 65):
            if time.perf_counter() >= _DEADLINE:
                break
            try:
                _, move = _search_root(you, opponent, depth, best_move)
                if move in legal and you[move] > 0:
                    best_move = move
            except _Timeout:
                break

        if best_move in legal and you[best_move] > 0:
            return best_move

    except Exception:
        pass

    if fallback in legal and you[fallback] > 0:
        return fallback
    return legal[0]
