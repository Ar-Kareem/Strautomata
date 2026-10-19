
import time

# Kalah policy: time-limited alpha-beta search with tactical evaluation.
# Board representation expected by policy:
# you = [h0, h1, h2, h3, h4, h5, store]
# opponent = [h0, h1, h2, h3, h4, h5, store]

_INF = 10 ** 30
_TERMINAL_SCALE = 10000

_EXACT = 0
_LOWER = 1
_UPPER = 2

# Conservative enough for a 1 second arena limit.
_TIME_LIMIT = 0.88

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _SearchTimeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """Return a legal move index 0..5."""
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        # The prompt says this never happens. Return an int anyway.
        return 0
    if len(legal) == 1:
        return legal[0]

    cur = tuple(int(x) for x in you)
    opp = tuple(int(x) for x in opponent)

    # Standard opening: pit 2 gives an immediate extra turn on 6x4 Kalah.
    if cur == (4, 4, 4, 4, 4, 4, 0) and opp == (4, 4, 4, 4, 4, 4, 0):
        return 2

    fallback = _greedy_move(cur, opp, legal)
    best_move = fallback

    global _DEADLINE, _NODES, _TT
    _DEADLINE = time.perf_counter() + _TIME_LIMIT
    _NODES = 0
    _TT = {}

    try:
        # Iterative deepening. Completed depths are always safe to use.
        for depth in range(1, 65):
            if time.perf_counter() >= _DEADLINE:
                break
            move, _val = _root_search(cur, opp, depth, best_move)
            if 0 <= move <= 5 and you[move] > 0:
                best_move = move
    except _SearchTimeout:
        pass
    except Exception:
        # Never risk an illegal/non-returning policy because of an unexpected bug.
        best_move = fallback

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return fallback


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()


def _house_sum(b):
    return b[0] + b[1] + b[2] + b[3] + b[4] + b[5]


def _terminal_value(cur, opp):
    ch = _house_sum(cur)
    oh = _house_sum(opp)
    if ch == 0 or oh == 0:
        return _TERMINAL_SCALE * ((cur[6] + ch) - (opp[6] + oh))
    return None


def _make_move(cur, opp, m):
    """
    Apply move m for cur against opp.
    Returns raw orientation: new_cur, new_opp, extra_turn.
    """
    c = list(cur)
    o = list(opp)

    n = c[m]
    c[m] = 0

    # The sowing cycle has 13 positions:
    # cur[0..5], cur store at 6, opp[0..5] at positions 7..12.
    q, r = divmod(n, 13)

    if q:
        for i in range(7):
            c[i] += q
        for i in range(6):
            o[i] += q

    pos = m
    for _ in range(r):
        pos += 1
        if pos == 13:
            pos = 0
        if pos <= 6:
            c[pos] += 1
        else:
            o[pos - 7] += 1

    last = (m + n) % 13

    # Capture.
    if last < 6 and c[last] == 1:
        oi = 5 - last
        if o[oi] > 0:
            c[6] += c[last] + o[oi]
            c[last] = 0
            o[oi] = 0

    return tuple(c), tuple(o), last == 6


def _capture_gain_for_move(side, other, m):
    """Approximate/compute immediate capture gain for side making move m."""
    n = side[m]
    if n <= 0:
        return 0

    last = (m + n) % 13
    if last >= 6:
        return 0

    q, r = divmod(n, 13)

    # Final count in landing house before capture.
    landing_base = 0 if last == m else side[last]
    landing_deposit = q + (1 if r else 0)
    if landing_base + landing_deposit != 1:
        return 0

    oi = 5 - last
    opp_pos = 7 + oi
    dist = (opp_pos - m) % 13
    opp_deposit = q + (1 if 1 <= dist <= r else 0)
    opp_final = other[oi] + opp_deposit

    if opp_final <= 0:
        return 0
    return opp_final + 1


def _side_features(side, other):
    legal = 0
    extras = 0
    cap_max = 0
    cap_sum = 0

    for m in range(6):
        n = side[m]
        if n <= 0:
            continue
        legal += 1
        last = (m + n) % 13
        if last == 6:
            extras += 1
        gain = _capture_gain_for_move(side, other, m)
        if gain:
            cap_sum += gain
            if gain > cap_max:
                cap_max = gain

    return legal, extras, cap_max, cap_sum


def _evaluate(cur, opp):
    """
    Static value from the current player-to-move's perspective.
    Terminal states are exact, including the final sweep.
    """
    ch = _house_sum(cur)
    oh = _house_sum(opp)

    if ch == 0 or oh == 0:
        return _TERMINAL_SCALE * ((cur[6] + ch) - (opp[6] + oh))

    store_diff = cur[6] - opp[6]
    house_diff = ch - oh

    # Seeds closer to own store are usually more valuable.
    pos_cur = (
        cur[0] + 2 * cur[1] + 3 * cur[2] +
        4 * cur[3] + 5 * cur[4] + 6 * cur[5]
    )
    pos_opp = (
        opp[0] + 2 * opp[1] + 3 * opp[2] +
        4 * opp[3] + 5 * opp[4] + 6 * opp[5]
    )

    l1, e1, cmax1, csum1 = _side_features(cur, opp)
    l2, e2, cmax2, csum2 = _side_features(opp, cur)

    score = 0
    score += 140 * store_diff
    score += 4 * house_diff
    score += 2 * (pos_cur - pos_opp)
    score += 26 * (e1 - e2)
    score += 9 * (cmax1 - cmax2)
    score += 2 * (csum1 - csum2)
    score += 3 * (l1 - l2)

    return score


def _order_score(cur, opp, m, c, o, extra):
    """Move ordering score from the mover's perspective."""
    ch = _house_sum(c)
    oh = _house_sum(o)

    if ch == 0 or oh == 0:
        return _TERMINAL_SCALE * ((c[6] + ch) - (o[6] + oh))

    store_gain = c[6] - cur[6]
    cap_gain = _capture_gain_for_move(cur, opp, m)

    score = 0
    score += 1200 * store_gain
    score += 3200 * cap_gain
    if extra:
        score += 50000
    score += m  # deterministic tie breaker, slightly prefers pits nearer store
    return score


def _ordered_moves(cur, opp, preferred=-1):
    moves = []
    for m in range(6):
        if cur[m] <= 0:
            continue
        c, o, extra = _make_move(cur, opp, m)
        s = _order_score(cur, opp, m, c, o, extra)
        if m == preferred:
            s += 10 ** 9
        moves.append((s, m, c, o, extra))

    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


def _root_search(cur, opp, depth, preferred):
    alpha = -_INF
    beta = _INF
    best_move = preferred
    best_val = -_INF

    for _ord, m, c, o, extra in _ordered_moves(cur, opp, preferred):
        if extra:
            val = _negamax(c, o, depth - 1, alpha, beta)
        else:
            val = -_negamax(o, c, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    return best_move, best_val


def _negamax(cur, opp, depth, alpha, beta):
    _check_time()

    tv = _terminal_value(cur, opp)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(cur, opp)

    key = cur + opp
    orig_alpha = alpha
    orig_beta = beta
    tt_best = -1

    entry = _TT.get(key)
    if entry is not None:
        stored_depth, stored_val, flag, stored_move = entry
        tt_best = stored_move
        if stored_depth >= depth:
            if flag == _EXACT:
                return stored_val
            if flag == _LOWER:
                if stored_val > alpha:
                    alpha = stored_val
            elif flag == _UPPER:
                if stored_val < beta:
                    beta = stored_val
            if alpha >= beta:
                return stored_val

    best_val = -_INF
    best_move = -1

    for _ord, m, c, o, extra in _ordered_moves(cur, opp, tt_best):
        if extra:
            val = _negamax(c, o, depth - 1, alpha, beta)
        else:
            val = -_negamax(o, c, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_move == -1:
        return _evaluate(cur, opp)

    if best_val <= orig_alpha:
        flag = _UPPER
    elif best_val >= orig_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    # Keep the table bounded.
    old = _TT.get(key)
    if len(_TT) < 300000 and (old is None or depth >= old[0]):
        _TT[key] = (depth, best_val, flag, best_move)

    return best_val


def _greedy_move(cur, opp, legal):
    """Safe fallback used if search times out before finishing."""
    best = legal[0]
    best_score = -_INF

    for m in legal:
        c, o, extra = _make_move(cur, opp, m)

        tv = _terminal_value(c, o)
        if tv is not None:
            score = tv
        else:
            if extra:
                score = _evaluate(c, o) + 1500
            else:
                score = -_evaluate(o, c)
            score += _order_score(cur, opp, m, c, o, extra) // 8

        if score > best_score:
            best_score = score
            best = m

    return best
