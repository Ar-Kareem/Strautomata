
import time

INF = 10**18
TERMINAL_SCALE = 10000
TIME_LIMIT = 0.92
TT_MAX = 150000

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
DEADLINE = 0.0
NODES = 0


class _Timeout(Exception):
    pass


def _house_sum(a):
    return a[0] + a[1] + a[2] + a[3] + a[4] + a[5]


def _pos_sum(a):
    return a[0] + 2 * a[1] + 3 * a[2] + 4 * a[3] + 5 * a[4] + 6 * a[5]


def _legal_count(a):
    return (
        (1 if a[0] > 0 else 0)
        + (1 if a[1] > 0 else 0)
        + (1 if a[2] > 0 else 0)
        + (1 if a[3] > 0 else 0)
        + (1 if a[4] > 0 else 0)
        + (1 if a[5] > 0 else 0)
    )


def _extra_count(a):
    c = 0
    for i in range(6):
        s = a[i]
        if s > 0 and ((i + s) % 13 == 6):
            c += 1
    return c


def _evaluate(you, opp, yh=None, oh=None):
    if yh is None:
        yh = _house_sum(you)
        oh = _house_sum(opp)

    # Terminal if one side is empty: sweep remaining seeds.
    if yh == 0:
        return (you[6] - (opp[6] + oh)) * TERMINAL_SCALE
    if oh == 0:
        return ((you[6] + yh) - opp[6]) * TERMINAL_SCALE

    sd = you[6] - opp[6]
    hd = yh - oh
    pd = _pos_sum(you) - _pos_sum(opp)
    ed = _extra_count(you) - _extra_count(opp)
    md = _legal_count(you) - _legal_count(opp)

    # Capture-trap structure:
    # empty houses opposite loaded enemy houses are potential future capture targets.
    td = 0
    for i in range(6):
        oi = 5 - i
        if you[i] == 0 and opp[oi] > 0:
            td += opp[oi]
        if opp[i] == 0 and you[oi] > 0:
            td -= you[oi]

    rem = yh + oh

    if rem <= 12:
        return 100 * sd + 12 * hd + 6 * ed + 2 * md + 2 * td
    if rem <= 24:
        return 82 * sd + 6 * hd + pd + 9 * ed + 2 * md + 2 * td
    return 70 * sd + 3 * hd + pd + 11 * ed + 2 * md + td


def _apply_move(you, opp, move):
    y = list(you)
    o = list(opp)

    seeds = y[move]
    y[move] = 0

    # Ring of 13 sowing positions from current player's perspective:
    # y0 y1 y2 y3 y4 y5 store o0 o1 o2 o3 o4 o5
    for step in range(1, seeds + 1):
        p = (move + step) % 13
        if p < 6:
            y[p] += 1
        elif p == 6:
            y[6] += 1
        else:
            o[p - 7] += 1

    last = (move + seeds) % 13
    extra = (last == 6)
    captured = 0

    if (not extra) and last < 6 and y[last] == 1 and o[5 - last] > 0:
        captured = 1 + o[5 - last]
        y[6] += captured
        y[last] = 0
        o[5 - last] = 0

    yh = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    oh = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]

    terminal = False
    if yh == 0 or oh == 0:
        if yh:
            y[6] += yh
            y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        if oh:
            o[6] += oh
            o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0
        terminal = True
        extra = False

    return tuple(y), tuple(o), extra, terminal, captured


def _ordered_moves(you, opp, tt_move=None):
    moves = []
    base_store = you[6]

    for i in range(6):
        if you[i] <= 0:
            continue

        ny, no, extra, terminal, captured = _apply_move(you, opp, i)

        if terminal:
            margin = ny[6] - no[6]
            order = 1_000_000 + 1000 * margin
        else:
            store_gain = ny[6] - base_store
            order = 200 * store_gain + 150 * captured
            if extra:
                order += 5000 + _evaluate(ny, no)
            else:
                order += -_evaluate(no, ny)

        if i == tt_move:
            order += 10_000_000

        moves.append((order, i, ny, no, extra, terminal, captured))

    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


def _search(you, opp, depth, alpha, beta):
    global NODES

    NODES += 1
    if (NODES & 127) == 0 and time.perf_counter() >= DEADLINE:
        raise _Timeout

    yh = _house_sum(you)
    oh = _house_sum(opp)

    if yh == 0 or oh == 0:
        return _evaluate(you, opp, yh, oh)

    rem = yh + oh
    solved_endgame = (rem <= 10)
    need_depth = 99 if solved_endgame else depth

    alpha0 = alpha
    beta0 = beta

    key = (you, opp)
    tt = TT.get(key)
    tt_move = None
    if tt is not None:
        tt_depth, tt_flag, tt_score, tt_move = tt
        if tt_depth >= need_depth:
            if tt_flag == EXACT:
                return tt_score
            if tt_flag == LOWER:
                if tt_score > alpha:
                    alpha = tt_score
            else:
                if tt_score < beta:
                    beta = tt_score
            if alpha >= beta:
                return tt_score

    if depth <= 0 and not solved_endgame:
        return _evaluate(you, opp, yh, oh)

    moves = _ordered_moves(you, opp, tt_move)
    if not moves:
        return _evaluate(you, opp, yh, oh)

    best = -INF
    best_move = moves[0][1]

    for _, move, ny, no, extra, terminal, captured in moves:
        if terminal:
            score = (ny[6] - no[6]) * TERMINAL_SCALE
        elif extra:
            score = _search(ny, no, depth, alpha, beta)
        else:
            score = -_search(no, ny, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = move

        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best <= alpha0:
        flag = UPPER
    elif best >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (need_depth, flag, best, best_move)
    return best


def _root_search(you, opp, depth):
    key = (you, opp)
    tt = TT.get(key)
    tt_move = tt[3] if tt is not None else None

    moves = _ordered_moves(you, opp, tt_move)
    if not moves:
        return 0, -INF

    alpha = -INF
    beta = INF
    best = -INF
    best_move = moves[0][1]

    for _, move, ny, no, extra, terminal, captured in moves:
        if time.perf_counter() >= DEADLINE:
            raise _Timeout

        if terminal:
            score = (ny[6] - no[6]) * TERMINAL_SCALE
        elif extra:
            score = _search(ny, no, depth, alpha, beta)
        else:
            score = -_search(no, ny, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = move

        if score > alpha:
            alpha = score

    TT[key] = (depth, EXACT, best, best_move)
    return best_move, best


def policy(you: list[int], opponent: list[int]) -> int:
    global DEADLINE, NODES, TT

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # Should not happen per spec.
    if len(legal) == 1:
        return legal[0]

    if len(TT) > TT_MAX:
        TT.clear()

    you_t = tuple(you)
    opp_t = tuple(opponent)

    root_tt = TT.get((you_t, opp_t))
    hint = root_tt[3] if root_tt is not None and root_tt[3] in legal else None

    # Strong legal fallback even if time is extremely tight.
    fallback_moves = _ordered_moves(you_t, opp_t, hint)
    best_move = fallback_moves[0][1] if fallback_moves else legal[0]

    NODES = 0
    DEADLINE = time.perf_counter() + TIME_LIMIT

    remaining = _house_sum(you_t) + _house_sum(opp_t)

    try:
        depth = 1
        while depth <= 24:
            move, score = _root_search(you_t, opp_t, depth)
            best_move = move

            # Root depth 1 is already exact when the remaining-seed endgame solver applies.
            if remaining <= 10:
                break

            depth += 1
    except _Timeout:
        pass

    # Absolute safety: always return a legal move.
    if you[best_move] > 0:
        return best_move
    return legal[0]
